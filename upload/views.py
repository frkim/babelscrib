from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceExistsError, AzureError
import os
import logging
from django.conf import settings

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
            
            # Get blob client and upload file
            blob_client = blob_service_client.get_blob_client(container=container_name, blob=file.name)
            blob_client.upload_blob(file, overwrite=True)
            
            logger.info(f"Successfully uploaded file: {file.name} for email: {email}")
            return JsonResponse({
                'message': 'File uploaded successfully',
                'filename': file.name,
                'container': container_name,
                'email': email
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