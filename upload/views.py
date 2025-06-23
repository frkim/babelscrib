from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError, AzureError, ResourceNotFoundError
import os
import logging
from django.conf import settings
from django.utils import timezone
import json
import urllib.parse
import mimetypes
# User isolation imports
from .models import Document
from .user_utils import UserIsolationService, require_user_session

logger = logging.getLogger(__name__)

# Add translation service imports (optional for testing)
try:
    from services.translation_service import create_translation_service
    from services.config import get_config
    TRANSLATION_AVAILABLE = True
except ImportError:
    TRANSLATION_AVAILABLE = False
    logger.warning("Translation services not available - storage test will skip translation tests")

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
        
        # Check Site configuration for django-allauth
        site_healthy = True
        site_error = None
        try:
            from django.contrib.sites.models import Site
            from django.conf import settings
            site = Site.objects.get(pk=getattr(settings, 'SITE_ID', 1))
            logger.debug(f"Site check passed: {site.domain}")
        except Site.DoesNotExist:
            site_healthy = False
            site_error = f"Site with ID {getattr(settings, 'SITE_ID', 1)} does not exist"
            logger.warning(site_error)
        except Exception as e:
            site_healthy = False
            site_error = f"Site check failed: {str(e)}"
            logger.warning(site_error)
        
        # Check SocialApp configuration for Microsoft auth
        socialapp_healthy = True
        socialapp_error = None
        try:
            from allauth.socialaccount.models import SocialApp
            microsoft_app = SocialApp.objects.get(provider='microsoft')
            # Check if it has valid client_id and is associated with a site
            if not microsoft_app.client_id or microsoft_app.client_id == 'your-client-id-here':
                socialapp_healthy = False
                socialapp_error = "Microsoft SocialApp has invalid client_id"
            elif not microsoft_app.sites.exists():
                socialapp_healthy = False
                socialapp_error = "Microsoft SocialApp is not associated with any site"
            else:
                logger.debug(f"SocialApp check passed: {microsoft_app.client_id[:8]}...")
        except SocialApp.DoesNotExist:
            socialapp_healthy = False
            socialapp_error = "Microsoft SocialApp does not exist"
            logger.warning(socialapp_error)
        except Exception as e:
            socialapp_healthy = False
            socialapp_error = f"SocialApp check failed: {str(e)}"
            logger.warning(socialapp_error)
        
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
            'status': 'healthy' if site_healthy and socialapp_healthy else 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'checks': {
                'database': 'ok',
                'site_config': 'ok' if site_healthy else 'error',
                'microsoft_auth': 'ok' if socialapp_healthy else 'error',
                'azure_storage': 'ok' if storage_healthy else ('warning' if connection_string else 'not_configured')
            }
        }
        
        # Add error details if any
        if site_error:
            health_status['checks']['site_config_error'] = site_error
        if socialapp_error:
            health_status['checks']['microsoft_auth_error'] = socialapp_error
        if storage_error:
            health_status['checks']['azure_storage_error'] = storage_error
        
        # Return 503 if critical systems (site/auth) are unhealthy
        # Storage issues are warnings since the app can still function
        status_code = 200 if site_healthy and socialapp_healthy else 503
        return JsonResponse(health_status, status=status_code)
        
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
@login_required
def upload_file(request):
    if request.method == 'POST':
        # Handle both single file and multiple files
        files = request.FILES.getlist('file') if 'file' in request.FILES else []
        email = request.POST.get('email', '').strip()
        
        if not files:
            return JsonResponse({'error': 'No files provided'}, status=400)
        
        if not email:
            return JsonResponse({'error': 'Email address is required'}, status=400)
        
        # Basic email validation
        import re
        email_regex = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        if not re.match(email_regex, email):
            return JsonResponse({'error': 'Invalid email address'}, status=400)
        
        # Create or update user session
        session_key = UserIsolationService.get_or_create_session(request, email)
        
        # For now, handle one file at a time (the frontend will call this endpoint multiple times)
        file = files[0] if files else None
        
        if not file:
            return JsonResponse({'error': 'No file provided'}, status=400)
        
        logger.info(f"Upload request from email: {email} for file: {file.name}")
        
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
            
            # Create user-specific blob name to ensure isolation
            user_blob_name = UserIsolationService.create_user_blob_name(email, file.name)
            
            # Get blob client and upload file with user-specific name
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=user_blob_name)
            blob_client.upload_blob(file, overwrite=True)
            
            # Save document record in database
            document = Document(
                title=file.name,
                user_email=email,
                blob_name=file.name,
                user_blob_name=user_blob_name
            )
            document.save()
            
            logger.info(f"Successfully uploaded file: {file.name} as {user_blob_name} for email: {email}")
            return JsonResponse({
                'message': 'File uploaded successfully',
                'filename': file.name,
                'container': container_name,
                'email': email,
                'session_key': session_key
            })
            
        except AzureError as e:
            logger.error(f"Azure error during upload: {str(e)}")
            return JsonResponse({'error': f'Storage error: {str(e)}'}, status=500)
        except Exception as e:
            logger.error(f"Unexpected error during upload: {str(e)}")
            return JsonResponse({'error': 'Upload failed'}, status=500)

    return JsonResponse({'error': 'Invalid request method'}, status=400)

@login_required
def index(request):
    context = {
        'user_email': request.user.email,
    }
    return render(request, 'upload/index.html', context)

@csrf_exempt
@require_user_session
def translate_documents(request):
    """Handle document translation requests."""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            target_language = data.get('target_language', 'en')
            source_language = data.get('source_language')  # Optional
            email = getattr(request, 'user_email', '')  # From decorator
            clear_target = data.get('clear_target', True)  # Default to True for automatic cleanup
            # Source cleanup is now always enabled automatically
            cleanup_source = True  # Always clean up source files automatically
            
            if not email:
                return JsonResponse({'error': 'User session required'}, status=401)
            
            logger.info(f"Translation request from email: {email} to language: {target_language}")
            if clear_target:
                logger.info("Target container will be cleared before translation")
            logger.info("Source files will be automatically cleaned up after translation")
            
            # Get user's documents
            user_documents = UserIsolationService.get_user_documents(request)
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
            
            # For user isolation, we need to create temporary containers or use a different approach
            # Since Azure Document Translation translates entire containers, we'll copy user files
            # to temporary containers for translation
            user_id_hash = UserIsolationService.generate_user_id_hash(email)
            
            # Create temporary container names for this translation session
            import uuid
            session_id = str(uuid.uuid4())[:8]
            temp_source_container = f"temp-source-{user_id_hash}-{session_id}"
            temp_target_container = f"temp-target-{user_id_hash}-{session_id}"
            
            # Get the base storage account URL from the config
            import urllib.parse
            source_uri_parts = urllib.parse.urlparse(config.source_uri)
            base_url = f"{source_uri_parts.scheme}://{source_uri_parts.netloc}"
            
            temp_source_uri = f"{base_url}/{temp_source_container}"
            temp_target_uri = f"{base_url}/{temp_target_container}"
            
            # Use the translation service with temporary containers
            result = translation_service.translate_user_documents_with_temp_containers(
                original_source_uri=config.source_uri,
                original_target_uri=config.target_uri,
                temp_source_uri=temp_source_uri,
                temp_target_uri=temp_target_uri,
                target_language=target_language,
                source_language=source_language,
                user_id_hash=user_id_hash,
                cleanup_source=cleanup_source
            )
            
            logger.info(f"Translation completed for {email}. Status: {result['status']}")
            
            # Include cleanup information in the response
            cleanup_message = ""
            
            # Old target files cleanup information
            old_target_cleanup = result.get('old_target_cleanup', {})
            if old_target_cleanup.get('cleanup_attempted'):
                old_files_cleaned = old_target_cleanup.get('cleaned_files', 0)
                old_files_found = old_target_cleanup.get('old_files_found', 0)
                old_files_failed = old_target_cleanup.get('failed_cleanups', 0)
                hours_threshold = old_target_cleanup.get('hours_threshold', 24)
                
                if old_files_found > 0:
                    cleanup_message += f" {old_files_cleaned} old target files (older than {hours_threshold}h) were removed."
                    if old_files_failed > 0:
                        cleanup_message += f" {old_files_failed} old target files failed to be removed."
                else:
                    cleanup_message += " No old target files found."
            
            # Source files cleanup information
            source_cleanup = result.get('source_cleanup', {})
            if source_cleanup.get('cleanup_attempted'):
                cleaned_count = source_cleanup.get('cleaned_files', 0)
                failed_count = source_cleanup.get('failed_cleanups', 0)
                if cleaned_count > 0:
                    cleanup_message += f" {cleaned_count} source files were cleaned up."
                if failed_count > 0:
                    cleanup_message += f" {failed_count} source files failed to be cleaned up."
            
            return JsonResponse({
                'success': True,
                'data': result,
                'message': f"Translation started successfully. Status: {result['status']}.{cleanup_message}"
            })
            
        except json.JSONDecodeError:
            return JsonResponse({'error': 'Invalid JSON payload'}, status=400)
        except Exception as e:
            error_message = str(e)
            email = getattr(request, 'user_email', 'unknown')
            logger.error(f'Translation error for {email}: {error_message}')
            
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
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)

@require_user_session
def download_file(request, filename):
    """Download a translated file from Azure Blob Storage with user isolation."""
    try:
        email = getattr(request, 'user_email', '')
        
        # Validate that the user can access this file
        if not UserIsolationService.validate_file_access(request, filename):
            logger.warning(f"Unauthorized file access attempt: {email} tried to access {filename}")
            raise Http404("File not found or access denied")
        
        # Get connection string from environment
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if not connection_string:
            logger.error("Azure Storage connection string not found")
            raise Http404("Storage configuration missing")
        
        # Debug and fix connection string if needed
        fixed_connection_string = debug_connection_string(connection_string)
        if not fixed_connection_string:
            logger.error("Invalid Azure Storage connection string format")
            raise Http404("Storage configuration invalid")
        
        # Initialize blob service client
        blob_service_client = BlobServiceClient.from_connection_string(fixed_connection_string)
        
        # Get target container name (where translated files are stored)
        container_name = os.getenv('AZURE_STORAGE_CONTAINER_NAME_TARGET', 'target')
        
        try:
            # Create user-specific blob name
            user_id_hash = UserIsolationService.generate_user_id_hash(email)
            user_blob_name = f"{user_id_hash}/{filename}"
            
            # Get blob client for the translated file
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=user_blob_name)
            
            # Check if blob exists
            if not blob_client.exists():
                logger.warning(f"File not found: {user_blob_name} in container: {container_name} for user: {email}")
                raise Http404("File not found")
            
            # Download the blob data
            blob_data = blob_client.download_blob()
            file_content = blob_data.readall()
            
            # Get blob properties for content type
            blob_properties = blob_client.get_blob_properties()
            content_type = blob_properties.content_settings.content_type
            
            # If content type is not set, try to guess from filename
            if not content_type:
                content_type, _ = mimetypes.guess_type(filename)
                if not content_type:
                    content_type = 'application/octet-stream'
            
            # Create HTTP response with file content
            response = HttpResponse(file_content, content_type=content_type)
            
            # Set download headers
            safe_filename = urllib.parse.quote(filename)
            response['Content-Disposition'] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{safe_filename}'
            response['Content-Length'] = len(file_content)
            
            # Clean up the translated file after successful download
            try:
                blob_client.delete_blob()
                logger.info(f"Successfully deleted translated file after download: {user_blob_name} for user: {email}")
                
                # Also update database record
                Document.objects.filter(
                    user_email=email,
                    user_blob_name__endswith=filename,
                    is_translated=True
                ).delete()
                
            except ResourceNotFoundError:
                # File was already deleted, this is not an error
                logger.info(f"Translated file {user_blob_name} was already deleted")
            except Exception as cleanup_error:
                # Log the cleanup error but don't fail the download
                logger.warning(f"Failed to delete translated file {user_blob_name} after download: {str(cleanup_error)}")
                # Continue with the download response despite cleanup failure
            
            logger.info(f"Successfully served file: {filename} to user: {email}")
            return response
            
        except ResourceNotFoundError:
            logger.warning(f"Blob not found: {user_blob_name} in container: {container_name} for user: {email}")
            raise Http404("File not found")
        except Exception as e:
            logger.error(f"Error downloading file {filename} for user {email}: {str(e)}")
            raise Http404("Error downloading file")
            
    except Exception as e:
        logger.error(f"Unexpected error in download_file: {str(e)}")
        raise Http404("Download failed")

@require_user_session
def list_user_files(request):
    """List all files belonging to the current user."""
    try:
        email = getattr(request, 'user_email', '')
        user_documents = UserIsolationService.get_user_documents(request)
        
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
        
        return JsonResponse({
            'success': True,
            'files': files_data,
            'count': len(files_data)
        })
        
    except Exception as e:
        logger.error(f"Error listing files for user: {str(e)}")
        return JsonResponse({'error': 'Failed to list files'}, status=500)

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

def test_microsoft(request):
    """Test view for Microsoft authentication"""
    from django.utils import timezone
    return render(request, 'basic_test.html', {
        'current_time': timezone.now()
    })