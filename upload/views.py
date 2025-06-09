from django.shortcuts import render
from django.http import JsonResponse, HttpResponse, Http404
from django.views.decorators.csrf import csrf_exempt
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError, AzureError, ResourceNotFoundError
import os
import logging
from django.conf import settings
# Add translation service imports
from lib.translation_service import create_translation_service
from lib.config import get_config
import json
import urllib.parse
import mimetypes
# User isolation imports
from .models import Document
from .user_utils import UserIsolationService, require_user_session

logger = logging.getLogger(__name__)

@csrf_exempt
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
            
            # Initialize blob service client
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            
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

def index(request):
    return render(request, 'upload/index.html')

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
                hours_threshold = old_target_cleanup.get('hours_threshold', 72)
                
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
        
        # Initialize blob service client
        blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        
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