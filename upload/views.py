from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError, AzureError, ResourceNotFoundError
import os
import logging
import re
import uuid
import time
import traceback
from django.conf import settings
from django.utils import timezone
import json
import urllib.parse
import mimetypes
import hashlib
from django.views.decorators.http import require_http_methods

# Document model imports
from .models import Document, UserSession
from .middleware import require_user_session

logger = logging.getLogger(__name__)

# Add translation service imports (optional for testing)
try:
    from services.translation_service import create_translation_service
    from services.config import get_config
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    logger.warning("Translation services not available - storage test will skip translation tests")

def create_user_hash(email):
    """Create a consistent hash from user email."""
    return hashlib.sha256(email.encode()).hexdigest()[:16]

def get_or_create_user_session(request, user_email):
    """
    Get or create a user session for the given email.
    """
    # Ensure we have a session key
    if not request.session.session_key:
        request.session.create()
    
    session_key = request.session.session_key
    user_id_hash = create_user_hash(user_email)
    
    # Get or create user session
    user_session, created = UserSession.objects.get_or_create(
        session_key=session_key,
        defaults={
            'user_email': user_email,
            'user_id_hash': user_id_hash,
        }
    )
    
    if not created:
        # Update existing session
        user_session.user_email = user_email
        user_session.user_id_hash = user_id_hash
        user_session.last_activity = timezone.now()
        user_session.save()
    
    # Add to request for this request
    request.user_email = user_email
    request.user_id_hash = user_id_hash
    request.user_session = user_session
    
    logger.info(f"User session {'created' if created else 'updated'} for {user_email}")
    return user_session

def debug_connection_string(connection_string):
    """Debug helper to safely log connection string issues without exposing sensitive data"""
    if not connection_string:
        logger.error("Connection string is None or empty")
        return False
    
    # Check for URL encoding issues
    if '%' in connection_string:
        logger.warning(f"Connection string contains URL encoding: {connection_string[:50]}...")
        # Try to decode it
        try:
            decoded = urllib.parse.unquote(connection_string)
            logger.info("Successfully decoded URL-encoded connection string")
            return decoded
        except Exception as e:
            logger.error(f"Failed to decode connection string: {e}")
            return False
    
    # Check for basic structure
    if 'DefaultEndpointsProtocol' not in connection_string:
        logger.error("Connection string doesn't contain DefaultEndpointsProtocol")
        return False
    
    if 'AccountName' not in connection_string:
        logger.error("Connection string doesn't contain AccountName")
        return False
        
    logger.info("Connection string appears to be properly formatted")
    return connection_string

def delete_user_documents(user_id_hash, user_email):
    """
    Delete all existing documents for a user from both database and Azure storage.
    Returns a dictionary with deletion results.
    """
    try:
        # Get user's documents
        user_documents = Document.objects.filter(user_id_hash=user_id_hash)
        
        if not user_documents.exists():
            logger.info(f"No existing documents found for user: {user_email}")
            return {
                'success': True,
                'message': 'No existing documents to delete',
                'deleted_count': 0,
                'blob_deletions': {'source': 0, 'target': 0}
            }
        
        document_count = user_documents.count()
        logger.info(f"Found {document_count} existing documents for user: {user_email}")
        
        # Get connection string for Azure Storage
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if not connection_string:
            logger.error("Azure Storage connection string not found")
            # Still delete from database even if blob deletion fails
            deleted_db_count = user_documents.count()
            user_documents.delete()
            return {
                'success': False,
                'message': 'Storage configuration missing, but database records deleted',
                'deleted_count': deleted_db_count,
                'blob_deletions': {'source': 0, 'target': 0}
            }
        
        # Debug and fix connection string if needed
        fixed_connection_string = debug_connection_string(connection_string)
        if not fixed_connection_string:
            logger.error("Invalid Azure Storage connection string format")
            # Still delete from database even if blob deletion fails
            deleted_db_count = user_documents.count()
            user_documents.delete()
            return {
                'success': False,
                'message': 'Storage configuration invalid, but database records deleted',
                'deleted_count': deleted_db_count,
                'blob_deletions': {'source': 0, 'target': 0}
            }
        
        # Initialize blob service client
        blob_service_client = BlobServiceClient.from_connection_string(fixed_connection_string)
        
        # Get container names
        source_container = os.getenv('AZURE_STORAGE_CONTAINER_NAME_SOURCE', 'source')
        target_container = os.getenv('AZURE_STORAGE_CONTAINER_NAME_TARGET', 'target')
        
        blob_deletions = {'source': 0, 'target': 0}
        
        # Delete blobs from Azure Storage
        for document in user_documents:
            # Delete from source container (original files)
            if document.user_blob_name:
                try:
                    source_blob_client = blob_service_client.get_blob_client(
                        container=source_container, 
                        blob=document.user_blob_name
                    )
                    source_blob_client.delete_blob()
                    blob_deletions['source'] += 1
                    logger.info(f"Deleted source blob: {document.user_blob_name}")
                except ResourceNotFoundError:
                    logger.warning(f"Source blob not found: {document.user_blob_name}")
                except Exception as e:
                    logger.error(f"Error deleting source blob {document.user_blob_name}: {str(e)}")
            
            # Delete from target container (translated files)
            # Try both with original filename and user-specific path
            target_blob_paths = [
                f"{user_id_hash}/{document.blob_name}",  # User-specific path with original filename
                f"{user_id_hash}/{document.title}",     # User-specific path with title
            ]
            
            for target_blob_path in target_blob_paths:
                try:
                    target_blob_client = blob_service_client.get_blob_client(
                        container=target_container, 
                        blob=target_blob_path
                    )
                    target_blob_client.delete_blob()
                    blob_deletions['target'] += 1
                    logger.info(f"Deleted target blob: {target_blob_path}")
                    break  # If one path works, don't try the others
                except ResourceNotFoundError:
                    # This is expected if the file doesn't exist or wasn't translated
                    continue
                except Exception as e:
                    logger.error(f"Error deleting target blob {target_blob_path}: {str(e)}")
        
        # Delete database records
        deleted_db_count = user_documents.count()
        user_documents.delete()
        
        logger.info(f"Successfully deleted {deleted_db_count} documents for user: {user_email}")
        logger.info(f"Blob deletions - Source: {blob_deletions['source']}, Target: {blob_deletions['target']}")
        
        return {
            'success': True,
            'message': f'Successfully deleted {deleted_db_count} existing documents',
            'deleted_count': deleted_db_count,
            'blob_deletions': blob_deletions
        }
        
    except Exception as e:
        logger.error(f"Error deleting user documents for {user_email}: {str(e)}")
        return {
            'success': False,
            'message': f'Error deleting existing documents: {str(e)}',
            'deleted_count': 0,
            'blob_deletions': {'source': 0, 'target': 0}
        }

def health_check(request):
    """
    Health check endpoint for monitoring and probes.
    Returns HTTP 200 if the application is healthy, 503 if unhealthy.
    """
    try:
        # Check database connectivity
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        # Check Azure Storage connectivity (optional - only if configured)
        storage_healthy = True
        storage_error = None
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if connection_string:
            try:
                # Debug and fix connection string if needed
                fixed_connection_string = debug_connection_string(connection_string)
                if not fixed_connection_string:
                    storage_healthy = False
                    storage_error = "Invalid Azure Storage connection string"
                else:
                    blob_service_client = BlobServiceClient.from_connection_string(fixed_connection_string)
                    # Try to list containers to verify connection
                    list(blob_service_client.list_containers(results_per_page=5))
            except Exception as e:
                logger.warning(f"Azure Storage health check failed: {str(e)}")
                storage_healthy = False
                storage_error = str(e)
        
        # Build health status
        health_status = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'checks': {
                'database': 'ok',
                'azure_storage': 'ok' if storage_healthy else ('warning' if connection_string else 'not_configured')
            }
        }
        
        # Add error details if any
        if storage_error:
            health_status['checks']['azure_storage_error'] = storage_error
        
        # Return 200 since we removed critical auth checks that could cause 503
        # Storage issues are warnings since the app can still function
        return JsonResponse(health_status, status=200)
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return JsonResponse({
            'status': 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        }, status=503)

def readiness_check(request):
    """
    Readiness check endpoint for Kubernetes-style probes.
    Returns HTTP 200 if the application is ready to serve traffic.
    """
    try:
        # Check if all required environment variables are set
        required_vars = ['SECRET_KEY']
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        
        if missing_vars:
            return JsonResponse({
                'status': 'not_ready',
                'timestamp': timezone.now().isoformat(),
                'error': f'Missing required environment variables: {missing_vars}'
            }, status=503)
        
        # Check database connectivity
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        return JsonResponse({
            'status': 'ready',
            'timestamp': timezone.now().isoformat()
        }, status=200)
        
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        return JsonResponse({
            'status': 'not_ready',
            'timestamp': timezone.now().isoformat(),
            'error': str(e)        }, status=503)

@csrf_exempt
def upload_file(request):
    if request.method == 'POST':
        # Debug logging to understand the request
        logger.info(f"Upload request received")
        logger.debug(f"Content-Type: {request.content_type}")
        logger.debug(f"POST data keys: {list(request.POST.keys())}")
        logger.debug(f"FILES data keys: {list(request.FILES.keys())}")
        # Get user email from form data - check both possible field names
        user_email = request.POST.get('user_email', '').strip()
        if not user_email:
            user_email = request.POST.get('email', '').strip()
        
        logger.debug(f"Extracted user_email: '{user_email}'")
        
        if not user_email:
            logger.error("No email found in request.POST")
            return JsonResponse({'error': 'User email is required'}, status=400)
        
        # Validate email format
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, user_email):
            return JsonResponse({'error': 'Invalid email format'}, status=400)
        
        # Create or update user session
        user_session = get_or_create_user_session(request, user_email)
        
        # Delete all existing documents for this user before uploading new ones
        user_id_hash = request.user_id_hash
        deletion_result = delete_user_documents(user_id_hash, user_email)
        
        if deletion_result['deleted_count'] > 0:
            logger.info(f"Deleted {deletion_result['deleted_count']} existing documents for user: {user_email}")
        
        # Handle both single file and multiple files
        files = request.FILES.getlist('file') if 'file' in request.FILES else []
        
        if not files:
            return JsonResponse({'error': 'No files provided'}, status=400)
        
        # For now, handle one file at a time (the frontend will call this endpoint multiple times)
        file = files[0] if files else None
        
        if not file:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        logger.info(f"Upload request for file: {file.name} by user: {user_email}")
        
        try:
            # Get connection string from environment
            connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            if not connection_string:
                logger.error("Azure Storage connection string not found")
                return JsonResponse({'error': 'Storage configuration missing'}, status=500)
            
            # Debug and fix connection string if needed
            fixed_connection_string = debug_connection_string(connection_string)
            if not fixed_connection_string:
                logger.error("Invalid Azure Storage connection string format")
                return JsonResponse({'error': 'Storage configuration invalid'}, status=500)
            
            # Initialize blob service client
            blob_service_client = BlobServiceClient.from_connection_string(fixed_connection_string)
            
            # Define container name (you can make this configurable)
            container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME_SOURCE', 'source')
            
            # Create container if it doesn't exist
            try:
                container_client = blob_service_client.get_container_client(container_name)
                container_client.create_container()
                logger.info(f"Created container: {container_name}")
            except ResourceExistsError:
                # Container already exists, which is fine
                logger.info(f"Container {container_name} already exists")
            except Exception as e:
                logger.error(f"Error creating container: {str(e)}")
                return JsonResponse({'error': 'Failed to create storage container'}, status=500)
            
            # Create user-specific blob name with user hash prefix
            user_id_hash = request.user_id_hash
            sanitized_filename = re.sub(r'[^\w\-_\.]', '_', file.name)
            user_blob_name = f"{user_id_hash}/{sanitized_filename}"
            
            # Get blob client and upload file
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=user_blob_name)
            blob_client.upload_blob(file, overwrite=True)
            
            # Save document record in database
            document = Document(
                title=file.name,
                user_email=user_email,
                user_id_hash=user_id_hash,
                blob_name=file.name,  # Original filename
                user_blob_name=user_blob_name  # User-specific blob name
            )
            document.save()
            
            logger.info(f"Successfully uploaded file: {file.name} as {user_blob_name} for user: {user_email}")
            
            response_data = {
                'message': 'File uploaded successfully',
                'filename': file.name,
                'container': container_name,
                'blob_name': user_blob_name,
                'user_email': user_email
            }
            
            # Add deletion information if documents were deleted
            if deletion_result['deleted_count'] > 0:
                response_data['previous_documents_deleted'] = {
                    'count': deletion_result['deleted_count'],
                    'message': deletion_result['message']
                }
            
            return JsonResponse(response_data)
            
        except AzureError as e:
            logger.error(f"Azure error during upload: {str(e)}")
            return JsonResponse({'error': f'Storage error: {str(e)}'}, status=500)
        except Exception as e:
            logger.error(f"Unexpected error during upload: {str(e)}")
            return JsonResponse({'error': 'Upload failed'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

def index(request):
    context = {}
    return render(request, 'upload/index.html', context)

@csrf_exempt
@csrf_exempt
def translate_documents(request):
    """Handle document translation requests with user isolation."""
    logger.info(f"Translation request received. Method: {request.method}")
    logger.debug(f"Request headers: {dict(request.headers)}")
    
    if request.method == 'POST':
        try:
            # Log raw request body for debugging
            logger.debug(f"Request body: {request.body}")
            
            data = json.loads(request.body)
            logger.info(f"Parsed JSON data: {data}")
            
            target_language = data.get('target_language', 'en')
            source_language = data.get('source_language')  # Optional
            clear_target = data.get('clear_target', True)  # Default to True for automatic cleanup
            cleanup_source = data.get('cleanup_source', False)  # Optional cleanup
            
            # Get user session information  
            if not hasattr(request, 'user_session') or not request.user_session:
                logger.error("No user session found")
                return JsonResponse({'error': 'Session error. Please refresh the page and try again.'}, status=400)
            
            user_email = request.user_email
            user_id_hash = request.user_id_hash
            
            logger.info(f"Translation request to language: {target_language} for user: {user_email}")
            if clear_target:
                logger.info("Target container will be cleared before translation")
            
            # Get user's documents only
            user_documents = Document.objects.filter(user_id_hash=user_id_hash)
            if not user_documents:
                return JsonResponse({'error': 'No documents found for translation'}, status=400)
            
            # Get configuration and create translation service
            try:
                config = get_config()
                translation_service = create_translation_service()
            except ValueError as config_error:
                logger.error(f"Configuration error: {str(config_error)}")
                return JsonResponse({
                    'error': f'Translation service configuration error: {str(config_error)}'
                }, status=500)
            
            # Use user-specific translation method
            result = translation_service.translate_documents_user_specific(
                user_id_hash=user_id_hash,
                target_language=target_language,
                source_language=source_language,
                clear_target=clear_target,
                cleanup_source=cleanup_source
            )
            
            # Update documents as translated
            user_documents.update(
                is_translated=True, 
                translation_language=target_language
            )
            
            logger.info(f"Translation completed for user {user_email}. Status: {result['status']}")
            logger.info(f"Translation result keys: {result.keys()}")
            logger.info(f"Documents in result: {result.get('documents', [])}")
            logger.info(f"Number of documents: {len(result.get('documents', []))}")
            
            # Log each document for debugging
            if 'documents' in result:
                for i, doc in enumerate(result['documents']):
                    logger.info(f"Document {i}: {doc}")
            
            return JsonResponse({
                'success': True,
                'data': result,
                'message': f"Translation started successfully. Status: {result['status']}"
            })
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}, Request body: {request.body}")
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
        except Exception as e:
            error_message = str(e)
            logger.error(f'Translation error for user {getattr(request, "user_email", "unknown")}: {error_message}')
            logger.error(f'Full exception: {repr(e)}')
            
            # Provide more user-friendly error messages
            if "TargetFileAlreadyExists" in error_message:
                return JsonResponse({
                    'error': 'Target files already exist. Please try again - the system will automatically clear previous translations.',
                    'retry_suggested': True
                }, status=409)  # Conflict status code
            else:
                return JsonResponse({
                    'error': f'Translation failed: {error_message}'
                }, status=500)
    else:
        logger.warning(f"Invalid request method for translation: {request.method}")
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@require_user_session
def download_file(request, filename):
    """Download a translated file from Azure Blob Storage with user isolation."""
    try:
        user_id_hash = request.user_id_hash
        user_email = request.user_email
        
        logger.info(f"Download request for file: {filename} by user: {user_email}")
        logger.debug(f"User ID hash: {user_id_hash}")
        
        # Verify file ownership - first try with exact filename
        document = None
        try:
            document = Document.objects.get(
                user_id_hash=user_id_hash,
                blob_name=filename
            )
            logger.info(f"Found document by blob_name: {filename}")
        except Document.DoesNotExist:
            # Try to find by title (original filename)
            try:
                document = Document.objects.get(
                    user_id_hash=user_id_hash,
                    title=filename
                )
                logger.info(f"Found document by title: {filename}")
            except Document.DoesNotExist:
                # List all user documents for debugging
                user_docs = Document.objects.filter(user_id_hash=user_id_hash)
                logger.warning(f"User {user_email} attempted to access unauthorized file: {filename}")
                logger.debug(f"Available documents for user: {[doc.blob_name for doc in user_docs]}")
                raise Http404("File not found or access denied")
        
        # Get connection string from environment
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if not connection_string:
            logger.error("Azure Storage connection string not found")
            raise Http404("Storage configuration missing")
        
        # Create blob service client
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
        # Try to find the file in user's target folder (translated files)
        target_container = os.getenv('AZURE_STORAGE_CONTAINER_NAME_TARGET', 'target')
        user_blob_path = f"{user_id_hash}/{filename}"
        
        logger.debug(f"Looking for translated file at: {target_container}/{user_blob_path}")
        
        try:
            blob_client = blob_service_client.get_blob_client(container=target_container, blob=user_blob_path)
            blob_data = blob_client.download_blob()
            
            # Create HTTP response with file data
            response = HttpResponse(blob_data.readall(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            logger.info(f"Successfully downloaded translated file: {filename} for user: {user_email}")
            return response
            
        except ResourceNotFoundError:
            logger.warning(f"Translated file not found at: {target_container}/{user_blob_path} for user: {user_email}")
            raise Http404("Translated file not found")
        except Exception as e:
            logger.error(f"Error downloading file {user_blob_path} for user {user_email}: {str(e)}")
            raise Http404("Download failed")
            
    except Exception as e:
        logger.error(f"Download error for {filename} by user {getattr(request, 'user_email', 'unknown')}: {str(e)}")
        raise Http404("Download failed")

@csrf_exempt
@require_user_session
def list_user_files(request):
    """List files for the current user only."""
    try:
        user_id_hash = request.user_id_hash
        user_email = request.user_email
        
        user_documents = Document.objects.filter(user_id_hash=user_id_hash).order_by('-uploaded_at')
        
        files_data = []
        for doc in user_documents:
            files_data.append({
                'id': doc.id,
                'filename': doc.blob_name,
                'title': doc.title,
                'uploaded_at': doc.uploaded_at.isoformat(),
                'is_translated': doc.is_translated,
                'translation_language': doc.translation_language
            })
        
        logger.info(f"Listed {len(files_data)} files for user: {user_email}")
        
        return JsonResponse({
            'success': True,
            'files': files_data,
            'count': len(files_data),
            'user_email': user_email
        })
        
    except Exception as e:
        logger.error(f"Error listing files for user {request.user_email}: {str(e)}")
        return JsonResponse({'error': 'Failed to list files'}, status=500)

@csrf_exempt
@csrf_exempt
def cleanup_sessions(request):
    """API endpoint to cleanup old sessions."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else {}
            hours = data.get('hours', 24)
            
            count = UserSession.cleanup_old_sessions(hours)
            
            return JsonResponse({
                'success': True,
                'message': f'Cleaned up {count} old sessions',
                'cleaned_count': count
            })
        except Exception as e:
            logger.error(f"Error cleaning up sessions: {str(e)}")
            return JsonResponse({'error': 'Session cleanup failed'}, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

def test_azure_storage(request):
    """
    Comprehensive Azure Storage connectivity test.
    Creates test files, verifies operations, and provides detailed error reporting.
    Supports both JSON API responses and HTML template rendering.
    """    # Check if JSON format is explicitly requested
    format_requested = request.GET.get('format', '').lower()
    is_json_request = (
        format_requested == 'json' or
        request.headers.get('Content-Type') == 'application/json' or
        request.headers.get('Accept') == 'application/json' or
        (hasattr(request, 'is_ajax') and request.is_ajax())
    )
    
    test_results = {
        'timestamp': timezone.now().isoformat(),
        'connection_string_status': 'unknown',
        'source_container_test': {},
        'target_container_test': {},
        'blob_operations': {},
        'overall_status': 'failed',
        'errors': [],
        'details': []
    }
    
    try:
        # Test 1: Check connection string
        test_results['details'].append("Testing Azure Storage connection string...")
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        
        if not connection_string:
            test_results['errors'].append("AZURE_STORAGE_CONNECTION_STRING environment variable not found")
            test_results['connection_string_status'] = 'missing'
            return _format_storage_test_response(test_results, is_json_request, request)
        
        # Debug and validate connection string
        fixed_connection_string = debug_connection_string(connection_string)
        
        if not fixed_connection_string:
            test_results['errors'].append("Invalid Azure Storage connection string format")
            test_results['connection_string_status'] = 'invalid'
            return _format_storage_test_response(test_results, is_json_request, request)
        
        test_results['connection_string_status'] = 'valid'
        test_results['details'].append("Connection string validation passed")
        
        # Test 2: Initialize blob service client
        test_results['details'].append("Initializing Azure Blob Service Client...")
        try:
            blob_service_client = BlobServiceClient.from_connection_string(fixed_connection_string)
            test_results['details'].append("Blob Service Client initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize Blob Service Client: {str(e)}"
            test_results['errors'].append(error_msg)
            test_results['details'].append(error_msg)
            return _format_storage_test_response(test_results, is_json_request, request)
        
        # Test 3: Test account connectivity
        test_results['details'].append("Testing account connectivity...")
        try:
            account_info = blob_service_client.get_account_information()
            # Handle both dict and object attribute access
            if hasattr(account_info, 'sku_name'):
                sku = account_info.sku_name
                kind = account_info.account_kind
            else:
                # If it's a dict or has different structure
                sku = getattr(account_info, 'sku_name', 'Unknown')
                kind = getattr(account_info, 'account_kind', 'Unknown')
            test_results['details'].append(f"Account info retrieved: SKU={sku}, Kind={kind}")
        except Exception as e:
            error_msg = f"Failed to retrieve account information: {str(e)}"
            test_results['errors'].append(error_msg)
            test_results['details'].append(error_msg)
            return _format_storage_test_response(test_results, is_json_request, request)
        
        # Test 4: Test source container operations
        source_container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME_SOURCE', 'source')
        test_results['details'].append(f"Testing source container: {source_container_name}")
        test_results['source_container_test'] = test_container_operations(
            blob_service_client, source_container_name, "source"
        )
        
        if test_results['source_container_test'].get('status') != 'success':
            test_results['errors'].extend(test_results['source_container_test'].get('errors', []))
        
        # Test 5: Test target container operations
        target_container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME_TARGET', 'target')
        test_results['details'].append(f"Testing target container: {target_container_name}")
        test_results['target_container_test'] = test_container_operations(
            blob_service_client, target_container_name, "target"
        )
        
        if test_results['target_container_test'].get('status') != 'success':
            test_results['errors'].extend(test_results['target_container_test'].get('errors', []))
        
        # Test 6: Test blob operations (create, read, delete)
        test_results['details'].append("Testing blob CRUD operations...")
        test_results['blob_operations'] = test_blob_crud_operations(
            blob_service_client, source_container_name
        )
        
        if test_results['blob_operations'].get('status') != 'success':
            test_results['errors'].extend(test_results['blob_operations'].get('errors', []))
          # Test 7: Test translation service configuration (if available)
        if TRANSLATION_AVAILABLE:
            test_results['details'].append("Testing translation service configuration...")
            translation_test = test_translation_service_config()
            test_results['translation_service'] = translation_test
            
            if translation_test.get('status') != 'success':
                test_results['errors'].extend(translation_test.get('errors', []))
        else:
            test_results['details'].append("Translation service testing skipped - services not available")
            test_results['translation_service'] = {
                'status': 'skipped',
                'details': ['Translation services not available in current configuration'],
                'operations': {'availability_check': 'skipped'}
            }
          # Determine overall status
        if not test_results['errors']:
            test_results['overall_status'] = 'success'
            test_results['details'].append("All Azure Storage tests passed successfully!")
        else:
            test_results['overall_status'] = 'failed'
            test_results['details'].append(f"Tests completed with {len(test_results['errors'])} errors")
        
        # Return appropriate response format
        return _format_storage_test_response(test_results, is_json_request, request)
            
    except Exception as e:
        error_msg = f"Unexpected error during storage test: {str(e)}"
        test_results['errors'].append(error_msg)
        test_results['details'].append(error_msg)
        test_results['overall_status'] = 'failed'
        
        # Add stack trace for debugging
        import traceback
        test_results['stack_trace'] = traceback.format_exc()
        
        logger.error(f"Azure Storage test failed: {error_msg}")
        logger.error(f"Stack trace: {traceback.format_exc()}")
        
        return _format_storage_test_response(test_results, is_json_request, request)

def _format_storage_test_response(test_results, is_json_request, request):
    """Helper function to format storage test response as JSON or HTML."""
    if is_json_request:
        status_code = 200 if test_results.get('overall_status') == 'success' else 500
        return JsonResponse(test_results, status=status_code)
    else:
        # Transform test_results for template consumption
        context = _transform_test_results_for_template(test_results)
        return render(request, 'upload/storage_test.html', context)

def _transform_test_results_for_template(test_results):
    """Transform raw test results into template-friendly format."""
    context = {'test_results': test_results}
    
    # Add some computed values for easier template rendering
    if test_results:
        context['test_results']['passed_tests'] = 0
        context['test_results']['failed_tests'] = len(test_results.get('errors', []))
        context['test_results']['warnings'] = 0
        context['test_results']['total_duration'] = 0.0
        
        # Count successful tests and calculate total duration
        for test_name, test_data in test_results.items():
            if isinstance(test_data, dict) and test_data.get('status') == 'success':
                context['test_results']['passed_tests'] += 1
            if isinstance(test_data, dict) and 'duration' in test_data:
                try:
                    context['test_results']['total_duration'] += float(test_data['duration'])
                except (ValueError, TypeError):
                    pass
        
        # Handle warnings (skipped tests)
        if test_results.get('translation_service', {}).get('status') == 'skipped':
            context['test_results']['warnings'] += 1
    
    return context

def test_container_operations(blob_service_client, container_name, container_type):
    """Test container-specific operations."""
    result = {
        'container_name': container_name,
        'container_type': container_type,
        'status': 'failed',
        'operations': {},
        'errors': [],
        'details': []
    }
    
    try:
        container_client = blob_service_client.get_container_client(container_name)
        
        # Test 1: Check if container exists
        result['details'].append(f"Checking if container '{container_name}' exists...")
        try:
            container_exists = container_client.exists()
            result['operations']['exists_check'] = 'success'
            result['details'].append(f"Container exists: {container_exists}")
        except Exception as e:
            error_msg = f"Failed to check container existence: {str(e)}"
            result['errors'].append(error_msg)
            result['operations']['exists_check'] = 'failed'
            result['details'].append(error_msg)
            return result
        
        # Test 2: Create container if it doesn't exist
        if not container_exists:
            result['details'].append(f"Creating container '{container_name}'...")
            try:
                container_client.create_container()
                result['operations']['create'] = 'success'
                result['details'].append(f"Container '{container_name}' created successfully")
            except Exception as e:
                error_msg = f"Failed to create container: {str(e)}"
                result['errors'].append(error_msg)
                result['operations']['create'] = 'failed'
                result['details'].append(error_msg)
                return result
        else:
            result['operations']['create'] = 'not_needed'
            result['details'].append(f"Container '{container_name}' already exists")
        
        # Test 3: List blobs in container
        result['details'].append(f"Listing blobs in container '{container_name}'...")
        try:
            blob_list = list(container_client.list_blobs(results_per_page=5))
            result['operations']['list_blobs'] = 'success'
            result['details'].append(f"Found {len(blob_list)} blobs in container")
            result['blob_count'] = len(blob_list)
        except Exception as e:
            error_msg = f"Failed to list blobs: {str(e)}"
            result['errors'].append(error_msg)
            result['operations']['list_blobs'] = 'failed'
            result['details'].append(error_msg)
            return result
        
        # Test 4: Get container properties
        result['details'].append(f"Getting container properties for '{container_name}'...")
        try:
            properties = container_client.get_container_properties()
            result['operations']['get_properties'] = 'success'
            result['details'].append(f"Container properties retrieved successfully")
            result['container_properties'] = {
                'creation_time': getattr(properties, 'creation_time', getattr(properties, 'created_on', None)),
                'last_modified': getattr(properties, 'last_modified', None),
                'lease_status': getattr(getattr(properties, 'lease', None), 'status', None),
                'public_access': getattr(properties, 'public_access', None)
            }
            # Convert datetime objects to strings if they exist
            if result['container_properties']['creation_time']:
                try:
                    result['container_properties']['creation_time'] = result['container_properties']['creation_time'].isoformat()
                except:
                    result['container_properties']['creation_time'] = str(result['container_properties']['creation_time'])
            if result['container_properties']['last_modified']:
                try:
                    result['container_properties']['last_modified'] = result['container_properties']['last_modified'].isoformat()
                except:
                    result['container_properties']['last_modified'] = str(result['container_properties']['last_modified'])
        except Exception as e:
            error_msg = f"Failed to get container properties: {str(e)}"
            result['errors'].append(error_msg)
            result['operations']['get_properties'] = 'failed'
            result['details'].append(error_msg)
            return result
        
        result['status'] = 'success'
        return result
        
    except Exception as e:
        error_msg = f"Unexpected error in container operations: {str(e)}"
        result['errors'].append(error_msg)
        result['details'].append(error_msg)
        return result

def test_blob_crud_operations(blob_service_client, container_name):
    """Test blob create, read, update, delete operations."""
    import uuid
    import time
    from datetime import datetime
    
    result = {
        'status': 'failed',
        'operations': {},
        'errors': [],
        'details': []
    }
    
    test_blob_name = f"test-blob-{uuid.uuid4().hex[:8]}-{int(time.time())}.txt"
    test_content = f"Test blob content created at {datetime.now().isoformat()}"
    
    try:
        blob_client = blob_service_client.get_blob_client(container=container_name, blob=test_blob_name)
        
        # Test 1: Create/Upload blob
        result['details'].append(f"Creating test blob: {test_blob_name}")
        try:
            blob_client.upload_blob(test_content, overwrite=True)
            result['operations']['create'] = 'success'
            result['details'].append(f"Test blob created successfully")
        except Exception as e:
            error_msg = f"Failed to create test blob: {str(e)}"
            result['errors'].append(error_msg)
            result['operations']['create'] = 'failed'
            result['details'].append(error_msg)
            return result
        
        # Test 2: Check if blob exists
        result['details'].append(f"Checking if test blob exists...")
        try:
            blob_exists = blob_client.exists()
            result['operations']['exists_check'] = 'success'
            result['details'].append(f"Blob exists: {blob_exists}")
            
            if not blob_exists:
                result['errors'].append("Test blob was created but existence check failed")
                return result
        except Exception as e:
            error_msg = f"Failed to check blob existence: {str(e)}"
            result['errors'].append(error_msg)
            result['operations']['exists_check'] = 'failed'
            result['details'].append(error_msg)
            return result
        
        # Test 3: Read blob content
        result['details'].append(f"Reading test blob content...")
        try:
            blob_data = blob_client.download_blob()
            downloaded_content = blob_data.readall().decode('utf-8')
            result['operations']['read'] = 'success'
            result['details'].append(f"Test blob content read successfully")
            
            # Verify content matches
            if downloaded_content == test_content:
                result['details'].append("Downloaded content matches uploaded content")
                result['operations']['content_verification'] = 'success'
            else:
                error_msg = "Downloaded content does not match uploaded content"
                result['errors'].append(error_msg)
                result['operations']['content_verification'] = 'failed'
                result['details'].append(error_msg)
        except Exception as e:
            error_msg = f"Failed to read test blob: {str(e)}"
            result['errors'].append(error_msg)
            result['operations']['read'] = 'failed'
            result['details'].append(error_msg)
            return result
        
        # Test 4: Get blob properties
        result['details'].append(f"Getting test blob properties...")
        try:
            properties = blob_client.get_blob_properties()
            result['operations']['get_properties'] = 'success'
            result['details'].append(f"Test blob properties retrieved successfully")
            result['blob_properties'] = {
                'size': properties.size,
                'content_type': properties.content_settings.content_type,
                'creation_time': properties.creation_time.isoformat() if properties.creation_time else None,
                'last_modified': properties.last_modified.isoformat() if properties.last_modified else None
            }
        except Exception as e:
            error_msg = f"Failed to get blob properties: {str(e)}"
            result['errors'].append(error_msg)
            result['operations']['get_properties'] = 'failed'
            result['details'].append(error_msg)
        
        # Test 5: Delete blob (cleanup)
        result['details'].append(f"Deleting test blob...")
        try:
            blob_client.delete_blob()
            result['operations']['delete'] = 'success'
            result['details'].append(f"Test blob deleted successfully")
        except Exception as e:
            error_msg = f"Failed to delete test blob: {str(e)}"
            result['errors'].append(error_msg)
            result['operations']['delete'] = 'failed'
            result['details'].append(error_msg)
            # Don't return here - this is cleanup, not critical for the test
        
        # Test 6: Verify blob is deleted
        result['details'].append(f"Verifying test blob deletion...")
        try:
            blob_exists_after_delete = blob_client.exists()
            if not blob_exists_after_delete:
                result['operations']['delete_verification'] = 'success'
                result['details'].append("Test blob deletion verified")
            else:
                result['operations']['delete_verification'] = 'failed'
                result['details'].append("Test blob still exists after deletion")
        except Exception as e:
            error_msg = f"Failed to verify blob deletion: {str(e)}"
            result['details'].append(error_msg)
            result['operations']['delete_verification'] = 'failed'
        
        # Check if all critical operations succeeded
        critical_operations = ['create', 'exists_check', 'read', 'content_verification']
        failed_critical = [op for op in critical_operations if result['operations'].get(op) != 'success']
        
        if not failed_critical:
            result['status'] = 'success'
            result['details'].append("All critical blob operations completed successfully")
        else:
            result['details'].append(f"Failed critical operations: {failed_critical}")
        
        return result
        
    except Exception as e:
        error_msg = f"Unexpected error in blob CRUD operations: {str(e)}"
        result['errors'].append(error_msg)
        result['details'].append(error_msg)
        return result

def test_translation_service_config():
    """Test translation service configuration."""
    result = {
        'status': 'failed',
        'operations': {},
        'errors': [],
        'details': []
    }
    
    if not TRANSLATION_AVAILABLE:
        result['status'] = 'skipped'
        result['details'].append("Translation services not available")
        result['operations']['availability_check'] = 'skipped'
        return result
    
    try:
        # Test 1: Check translation service configuration
        result['details'].append("Testing translation service configuration...")
        try:
            config = get_config()
            result['operations']['get_config'] = 'success'
            result['details'].append("Translation config retrieved successfully")
            
            # Test config properties
            result['config_details'] = {
                'endpoint': config.endpoint,
                'source_uri': config.source_uri,
                'target_uri': config.target_uri,
                'key_configured': bool(os.getenv('AZURE_TRANSLATION_KEY'))
            }
            
        except Exception as e:
            error_msg = f"Failed to get translation config: {str(e)}"
            result['errors'].append(error_msg)
            result['operations']['get_config'] = 'failed'
            result['details'].append(error_msg)
            return result
        
        # Test 2: Try to create translation service
        result['details'].append("Testing translation service creation...")
        try:
            translation_service = create_translation_service()
            result['operations']['create_service'] = 'success'
            result['details'].append("Translation service created successfully")
        except Exception as e:
            error_msg = f"Failed to create translation service: {str(e)}"
            result['errors'].append(error_msg)
            result['operations']['create_service'] = 'failed'
            result['details'].append(error_msg)
            return result
        
        result['status'] = 'success'
        return result
        
    except Exception as e:
        error_msg = f"Unexpected error in translation service test: {str(e)}"
        result['errors'].append(error_msg)
        result['details'].append(error_msg)
        return result

# Debug endpoint for checking user files and translation service
@csrf_exempt
@require_user_session
def debug_user_files(request):
    """Debug endpoint to check user files and translation service status."""
    try:
        user_email = request.user_email
        user_id_hash = request.user_id_hash
        
        # Check database files
        user_documents = Document.objects.filter(user_id_hash=user_id_hash)
        db_files = [{"id": doc.id, "filename": doc.blob_name, "title": doc.title} for doc in user_documents]
        
        # Check translation service
        from services.translation_service import create_translation_service
        translation_service = create_translation_service()
        
        # Check if user has source files in blob storage
        source_uri = os.getenv('AZURE_TRANSLATION_SOURCE_URI')
        has_source_files = translation_service._user_has_source_files(source_uri, user_id_hash)
        
        # List actual files in blob storage
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        container_client = blob_service_client.get_container_client('source')
        
        blob_files = []
        for blob in container_client.list_blobs(name_starts_with=f"{user_id_hash}/"):
            blob_files.append(blob.name)
        
        return JsonResponse({
            'user_email': user_email,
            'user_id_hash': user_id_hash,
            'database_files': db_files,
            'blob_storage_files': blob_files,
            'has_source_files_check': has_source_files,
            'source_uri': source_uri
        })
        
    except Exception as e:
        logger.error(f"Debug endpoint error: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
def delete_translated_documents(request):
    """Delete all translated documents from Azure Storage and clear UI state."""
    if request.method == 'POST':
        try:
            logger.info("Delete translated documents request received")
            
            # Get Azure storage connection
            connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            if not connection_string:
                return JsonResponse({'error': 'Azure Storage connection not configured'}, status=500)
            
            target_container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME_TARGET', 'target')
            
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            container_client = blob_service_client.get_container_client(target_container_name)
            
            # List and delete all blobs in the target container
            deleted_count = 0
            deleted_files = []
            
            blob_list = container_client.list_blobs()
            for blob in blob_list:
                try:
                    blob_client = container_client.get_blob_client(blob.name)
                    blob_client.delete_blob()
                    deleted_count += 1
                    deleted_files.append(blob.name)
                    logger.info(f"Deleted translated file: {blob.name}")
                except Exception as e:
                    logger.warning(f"Failed to delete blob {blob.name}: {str(e)}")
            
            # Update database - mark all documents as not translated
            updated_docs = Document.objects.filter(is_translated=True).update(
                is_translated=False,
                translation_language=None
            )
            
            logger.info(f"Deleted {deleted_count} translated files and updated {updated_docs} database records")
            
            return JsonResponse({
                'success': True,
                'message': f'Deleted {deleted_count} translated documents',
                'deleted_count': deleted_count,
                'deleted_files': deleted_files,
                'updated_records': updated_docs
            })
            
        except Exception as e:
            logger.error(f"Error deleting translated documents: {str(e)}")
            return JsonResponse({
                'error': f'Failed to delete translated documents: {str(e)}'
            }, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@csrf_exempt
@require_user_session
def delete_individual_translated_document(request, filename):
    """Delete a specific translated document from Azure Storage."""
    logger.info(f"Delete individual document request received - Method: {request.method}, Filename: {filename}")
    
    if request.method == 'POST':
        try:
            # Check if user session exists
            if not hasattr(request, 'user_id_hash') or not hasattr(request, 'user_email'):
                logger.error("User session not found in delete request")
                return JsonResponse({'error': 'User session not found. Please refresh and try again.'}, status=400)
            
            user_id_hash = request.user_id_hash
            user_email = request.user_email
            
            logger.info(f"Delete individual translated document request for: {filename} by user: {user_email}")
            logger.info(f"User ID hash: {user_id_hash}")
            
            # Verify file ownership
            document = None
            try:
                # First try to find by exact blob_name match
                document = Document.objects.get(
                    user_id_hash=user_id_hash,
                    blob_name=filename
                )
                logger.info(f"Found document by exact blob_name: {filename}")
            except Document.DoesNotExist:
                try:
                    # Try to find by title (original filename)
                    document = Document.objects.get(
                        user_id_hash=user_id_hash,
                        title=filename
                    )
                    logger.info(f"Found document by title: {filename}")
                except Document.DoesNotExist:
                    # Try to find by blob_name ending with the filename (in case of path)
                    try:
                        document = Document.objects.get(
                            user_id_hash=user_id_hash,
                            blob_name__endswith=filename
                        )
                        logger.info(f"Found document by blob_name ending with: {filename}")
                    except Document.DoesNotExist:
                        logger.warning(f"Document not found for user {user_email}: {filename}")
                        return JsonResponse({'error': 'File not found or access denied'}, status=404)
            
            # Get Azure storage connection
            connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
            if not connection_string:
                logger.error("Azure Storage connection string not found")
                return JsonResponse({'error': 'Azure Storage connection not configured'}, status=500)
            
            target_container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME_TARGET', 'target')
            logger.info(f"Using target container: {target_container_name}")
            
            # Create blob service client
            try:
                blob_service_client = BlobServiceClient.from_connection_string(connection_string)
                container_client = blob_service_client.get_container_client(target_container_name)
            except Exception as e:
                logger.error(f"Failed to create blob service client: {str(e)}")
                return JsonResponse({'error': f'Storage connection failed: {str(e)}'}, status=500)
            
            # Delete the specific file from Azure Storage
            # The blob path should be user_id_hash/filename
            # But the filename parameter might already include the path or just be the filename
            if '/' in filename:
                # If filename includes path, use as-is
                user_blob_path = filename
            else:
                # If filename is just the filename, construct the full path
                user_blob_path = f"{user_id_hash}/{filename}"
            
            logger.info(f"Attempting to delete blob: {user_blob_path}")
            
            try:
                blob_client = container_client.get_blob_client(user_blob_path)
                blob_client.delete_blob()
                logger.info(f"Successfully deleted translated file: {user_blob_path} for user: {user_email}")
                
                # Update database - mark document as not translated
                document.is_translated = False
                document.translation_language = None
                document.save()
                logger.info(f"Updated database for document: {filename}")
                
                return JsonResponse({
                    'success': True,
                    'message': f'Successfully deleted {filename}',
                    'filename': filename
                })
                
            except ResourceNotFoundError:
                logger.warning(f"Translated file not found in storage: {user_blob_path} for user: {user_email}")
                return JsonResponse({'error': 'Translated file not found in storage'}, status=404)
            except AzureError as e:
                logger.error(f"Azure error deleting file {user_blob_path} for user {user_email}: {str(e)}")
                return JsonResponse({'error': f'Azure storage error: {str(e)}'}, status=500)
            except Exception as e:
                logger.error(f"Unexpected error deleting file {user_blob_path} for user {user_email}: {str(e)}")
                return JsonResponse({'error': f'Failed to delete file: {str(e)}'}, status=500)
            
        except Exception as e:
            logger.error(f"Error in delete_individual_translated_document for {filename}: {str(e)}")
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception traceback: {traceback.format_exc()}")
            return JsonResponse({
                'error': f'Failed to delete translated document: {str(e)}'
            }, status=500)
    
    logger.warning(f"Invalid request method for delete: {request.method}")
    return JsonResponse({'error': 'Invalid request method'}, status=405)