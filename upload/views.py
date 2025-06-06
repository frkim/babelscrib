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
    if request.method == 'POST' and request.FILES['file']:
        file = request.FILES['file']
        
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
            
            logger.info(f"Successfully uploaded file: {file.name}")
            return JsonResponse({
                'message': 'File uploaded successfully',
                'filename': file.name,
                'container': container_name
            })
            
        except AzureError as e:
            logger.error(f"Azure error during upload: {str(e)}")
            return JsonResponse({'error': f'Storage error: {str(e)}'}, status=500)
        except Exception as e:
            logger.error(f"Unexpected error during upload: {str(e)}")
            return JsonResponse({'error': 'Upload failed'}, status=500)

    return JsonResponse({'error': 'Invalid request'}, status=400)

def index(request):
    return render(request, 'upload/index.html')