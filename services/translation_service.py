"""
Document Translation Service Library

This module provides a reusable service for translating documents using Azure Cognitive Services.
"""

from azure.core.credentials import AzureKeyCredential
from azure.ai.translation.document import DocumentTranslationClient, DocumentTranslationInput, TranslationTarget
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import ResourceNotFoundError
from typing import Dict, List, Optional, Any
import logging
import os
from datetime import datetime, timedelta, timezone
from .config import get_config


class DocumentTranslationService:
    """
    A service class for handling document translation using Azure Document Translation API.
    """
    
    def __init__(self, key: str, endpoint: str):
        """
        Initialize the DocumentTranslationService.
        
        Args:
            key (str): Azure Cognitive Services API key
            endpoint (str): Azure Cognitive Services endpoint URL
        """
        if not key:
            raise ValueError("Azure Cognitive Services API key is required")
        if not endpoint:
            raise ValueError("Azure Cognitive Services endpoint is required")
            
        self.key = key
        self.endpoint = endpoint
        self.client = DocumentTranslationClient(endpoint, AzureKeyCredential(key))
        self.logger = logging.getLogger(__name__)
          # Initialize blob service client for target container management
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        if connection_string:
            self.blob_service_client = BlobServiceClient.from_connection_string(connection_string)
        else:
            self.blob_service_client = None
            self.logger.warning("Azure Storage connection string not found - target file cleanup will be skipped")
    
    def translate_documents(
        self, 
        source_uri: str, 
        target_uri: str, 
        target_language: str,
        source_language: Optional[str] = None,
        clear_target: bool = True
    ) -> Dict[str, Any]:
        """
        Translate documents from source container to target container.
        
        Args:
            source_uri (str): URI of the source blob container
            target_uri (str): URI of the target blob container
            target_language (str): Target language code (e.g., 'en', 'es', 'fr')
            source_language (str, optional): Source language code. If not provided, auto-detection is used.
            clear_target (bool, optional): Whether to clear target container before translation. Defaults to True.
        
        Returns:
            Dict[str, Any]: Translation results including status, document details, and translated documents
        
        Raises:
            Exception: If translation operation fails
        """
        try:
            self.logger.info(f"Starting document translation from {source_uri} to {target_uri}")
            self.logger.info(f"Target language: {target_language}")
              # Clear target container if requested to prevent TargetFileAlreadyExists errors
            if clear_target:
                self.logger.info("Clearing target container to prevent conflicts...")
                if not self._clear_target_container(target_uri):
                    self.logger.warning("Failed to clear target container, proceeding anyway...")
            
            # Create translation target
            translation_target = TranslationTarget(target_url=target_uri, language=target_language)
            
            # Create document translation input
            if source_language:
                # If source language is specified, include it
                document_translation_input = DocumentTranslationInput(
                    source_url=source_uri,
                    targets=[translation_target],
                    source_language=source_language
                )
            else:
                # Auto-detect source language
                document_translation_input = DocumentTranslationInput(
                    source_url=source_uri,
                    targets=[translation_target]
                )
            
            # Start the translation operation
            poller = self.client.begin_translation([document_translation_input])
            
            # Wait for completion and get results
            result = poller.result()
            
            # Prepare response data
            response = {
                'status': poller.status(),
                'created_on': poller.details.created_on,
                'last_updated_on': poller.details.last_updated_on,
                'total_documents': poller.details.documents_total_count,
                'failed_documents': poller.details.documents_failed_count,
                'succeeded_documents': poller.details.documents_succeeded_count,
                'documents': []
            }            # Process individual document results
            for document in result:
                # Extract filename from source document URL
                source_url = document.source_document_url if hasattr(document, 'source_document_url') else None
                translated_url = document.translated_document_url if document.status == 'Succeeded' else None
                
                source_filename = self._extract_filename_from_url(source_url)
                translated_filename = self._extract_filename_from_url(translated_url)
                
                # Try alternative filename extraction methods if URLs don't work
                if not source_filename and hasattr(document, 'source_document_name'):
                    source_filename = document.source_document_name
                
                if not translated_filename and hasattr(document, 'translated_document_name'):
                    translated_filename = document.translated_document_name
                
                # Log for debugging
                self.logger.info(f"Document ID: {document.id}")
                self.logger.info(f"Source URL: {source_url}")
                self.logger.info(f"Translated URL: {translated_url}")
                self.logger.info(f"Source filename: {source_filename}")
                self.logger.info(f"Translated filename: {translated_filename}")
                
                # Log all available document attributes for debugging
                self.logger.info(f"Document attributes: {[attr for attr in dir(document) if not attr.startswith('_')]}")
                
                doc_info = {
                    'id': document.id,
                    'status': document.status,
                    'source_filename': source_filename,
                    'translated_filename': translated_filename,
                    'source_document_url': source_url,
                    'translated_document_url': translated_url,
                    'translated_to': document.translated_to if document.status == 'Succeeded' else None,
                    'error': {
                        'code': document.error.code if hasattr(document, 'error') and document.error else None,
                        'message': document.error.message if hasattr(document, 'error') and document.error else None
                    } if document.status != 'Succeeded' else None
                }
                response['documents'].append(doc_info)
            
            self.logger.info(f"Translation completed. Status: {response['status']}")
            self.logger.info(f"Total: {response['total_documents']}, Succeeded: {response['succeeded_documents']}, Failed: {response['failed_documents']}")
            
            return response
            
        except Exception as e:
            self.logger.error(f"Translation operation failed: {str(e)}")
            raise Exception(f"Document translation failed: {str(e)}")
    
    def _clear_target_container(self, target_uri: str) -> bool:
        """
        Clear all files from the target container to prevent translation conflicts.
        
        Args:
            target_uri (str): URI of the target blob container
        
        Returns:
            bool: True if clearing was successful or not needed, False if failed
        """
        if not self.blob_service_client:
            self.logger.warning("Blob service client not available - skipping target container cleanup")
            return True
        
        try:
            # Extract container name from URI
            # Expected format: https://account.blob.core.windows.net/container
            uri_parts = target_uri.rstrip('/').split('/')
            if len(uri_parts) < 4:
                self.logger.error(f"Invalid target URI format: {target_uri}")
                return False
            
            container_name = uri_parts[-1]
            self.logger.info(f"Clearing target container: {container_name}")
            
            # Get container client
            container_client = self.blob_service_client.get_container_client(container_name)
            
            # List all blobs in the container
            blob_list = container_client.list_blobs()
            deleted_count = 0
            
            for blob in blob_list:
                try:
                    # Delete each blob
                    blob_client = container_client.get_blob_client(blob.name)
                    blob_client.delete_blob()
                    deleted_count += 1
                    self.logger.debug(f"Deleted blob: {blob.name}")
                except ResourceNotFoundError:
                    # Blob was already deleted, continue
                    self.logger.debug(f"Blob {blob.name} was already deleted")
                except Exception as e:
                    self.logger.warning(f"Failed to delete blob {blob.name}: {str(e)}")
                    # Continue with other blobs even if one fails
            
            if deleted_count > 0:
                self.logger.info(f"Successfully cleared {deleted_count} files from target container {container_name}")
            else:
                self.logger.info(f"Target container {container_name} was already empty")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to clear target container: {str(e)}")
            return False
    
    def get_translation_status(self, operation_id: str) -> Dict[str, Any]:
        """
        Get the status of a specific translation operation.
        
        Args:
            operation_id (str): The operation ID returned from a translation request
        
        Returns:
            Dict[str, Any]: Operation status and details
        """
        try:
            # This would require storing operation IDs and implementing status checking
            # For now, this is a placeholder for future implementation
            pass
        except Exception as e:
            self.logger.error(f"Failed to get translation status: {str(e)}")
            raise Exception(f"Failed to get translation status: {str(e)}")
    
    def list_supported_languages(self) -> List[Dict[str, str]]:
        """
        Get list of supported languages for translation.
        
        Returns:
            List[Dict[str, str]]: List of supported language codes and names
        """
        try:
            # This would require implementing language listing functionality
            # For now, return common language codes
            return [
                {'code': 'en', 'name': 'English'},
                {'code': 'es', 'name': 'Spanish'},
                {'code': 'fr', 'name': 'French'},
                {'code': 'de', 'name': 'German'},
                {'code': 'it', 'name': 'Italian'},
                {'code': 'pt', 'name': 'Portuguese'},
                {'code': 'zh', 'name': 'Chinese'},
                {'code': 'ja', 'name': 'Japanese'},
                {'code': 'ko', 'name': 'Korean'},
                {'code': 'ar', 'name': 'Arabic'},
                {'code': 'ru', 'name': 'Russian'},                {'code': 'hi', 'name': 'Hindi'}            ]
        except Exception as e:
            self.logger.error(f"Failed to get supported languages: {str(e)}")
            raise Exception(f"Failed to get supported languages: {str(e)}")
    
    def cleanup_source_files(self, source_uri: str, document_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Clean up source files from blob storage after translation (successful or unsuccessful).
        
        Args:
            source_uri (str): URI of the source blob container
            document_results (List[Dict[str, Any]]): List of document translation results
        
        Returns:
            Dict[str, Any]: Cleanup results including success/failure counts
        """
        if not self.blob_service_client:
            self.logger.warning("Blob service client not available - skipping source file cleanup")
            return {
                'cleanup_attempted': False,
                'reason': 'Blob service client not available',
                'cleaned_files': 0,
                'failed_cleanups': 0,
                'errors': []
            }
        
        try:
            # Extract container name from URI
            uri_parts = source_uri.rstrip('/').split('/')
            if len(uri_parts) < 4:
                self.logger.error(f"Invalid source URI format: {source_uri}")
                return {
                    'cleanup_attempted': False,
                    'reason': f'Invalid source URI format: {source_uri}',
                    'cleaned_files': 0,
                    'failed_cleanups': 0,
                    'errors': []
                }
            
            container_name = uri_parts[-1]
            self.logger.info(f"Starting cleanup of source container: {container_name}")
            
            # Get container client
            container_client = self.blob_service_client.get_container_client(container_name)
            
            cleaned_files = 0
            failed_cleanups = 0
            cleanup_errors = []
            
            # Process each document result to clean up the corresponding source file
            for doc_result in document_results:
                source_filename = doc_result.get('source_filename')
                
                if not source_filename:
                    self.logger.warning(f"No source filename found for document ID: {doc_result.get('id', 'unknown')}")
                    continue
                
                try:
                    # Get blob client for the source file
                    blob_client = container_client.get_blob_client(source_filename)
                    
                    # Check if blob exists before attempting deletion
                    if blob_client.exists():
                        # Delete the source file
                        blob_client.delete_blob()
                        cleaned_files += 1
                        self.logger.info(f"Successfully deleted source file: {source_filename}")
                    else:
                        self.logger.info(f"Source file {source_filename} was already deleted or doesn't exist")
                        
                except ResourceNotFoundError:
                    # File was already deleted, this is not an error
                    self.logger.info(f"Source file {source_filename} was already deleted")
                except Exception as e:
                    failed_cleanups += 1
                    error_msg = f"Failed to delete source file {source_filename}: {str(e)}"
                    cleanup_errors.append(error_msg)
                    self.logger.error(error_msg)
            
            cleanup_result = {
                'cleanup_attempted': True,
                'cleaned_files': cleaned_files,
                'failed_cleanups': failed_cleanups,
                'errors': cleanup_errors,
                'container_name': container_name
            }
            
            if cleaned_files > 0:
                self.logger.info(f"Source cleanup completed: {cleaned_files} files deleted, {failed_cleanups} failures")
            else:
                self.logger.info("No source files were found to delete")
            
            return cleanup_result
            
        except Exception as e:
            error_msg = f"Failed to cleanup source files: {str(e)}"
            self.logger.error(error_msg)
            return {
                'cleanup_attempted': False,
                'reason': error_msg,                'cleaned_files': 0,                'failed_cleanups': 0,
                'errors': [error_msg]
            }

    def translate_documents_with_cleanup(
        self, 
        source_uri: str, 
        target_uri: str, 
        target_language: str,
        source_language: Optional[str] = None,
        clear_target: bool = True,
        cleanup_source: bool = False,
        cleanup_old_target_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Translate documents and optionally clean up source files after completion.
        Also automatically cleans up old target files before translation.
        
        Args:
            source_uri (str): URI of the source blob container
            target_uri (str): URI of the target blob container
            target_language (str): Target language code (e.g., 'en', 'es', 'fr')
            source_language (str, optional): Source language code. If not provided, auto-detection is used.
            clear_target (bool, optional): Whether to clear target container before translation. Defaults to True.
            cleanup_source (bool, optional): Whether to clean up source files after translation. Defaults to False.
            cleanup_old_target_hours (int, optional): Hours threshold for cleaning up old target files. Defaults to 24 hours (1 day).
        
        Returns:
            Dict[str, Any]: Translation results including cleanup information
        """
        # First, clean up old target files (older than specified hours)
        self.logger.info(f"Starting automatic cleanup of old target files (older than {cleanup_old_target_hours} hours)")
        old_target_cleanup_result = self.cleanup_old_target_files(target_uri, cleanup_old_target_hours)
        
        # Log old target cleanup summary
        if old_target_cleanup_result['cleanup_attempted']:
            old_files_cleaned = old_target_cleanup_result['cleaned_files']
            old_files_failed = old_target_cleanup_result['failed_cleanups']
            old_files_found = old_target_cleanup_result['old_files_found']
            self.logger.info(f"Old target files cleanup summary: {old_files_found} old files found, "
                           f"{old_files_cleaned} files deleted, {old_files_failed} failures")
        else:
            self.logger.warning(f"Old target files cleanup was not performed: {old_target_cleanup_result.get('reason', 'Unknown reason')}")
        
        # Perform the translation
        translation_result = self.translate_documents(
            source_uri=source_uri,
            target_uri=target_uri,
            target_language=target_language,
            source_language=source_language,
            clear_target=clear_target
        )
        
        # Add cleanup information to the result
        translation_result['cleanup_source_requested'] = cleanup_source
        translation_result['old_target_cleanup'] = old_target_cleanup_result
        
        # Clean up source files if requested
        if cleanup_source:
            self.logger.info("Starting source file cleanup after translation")
            cleanup_result = self.cleanup_source_files(source_uri, translation_result['documents'])
            translation_result['source_cleanup'] = cleanup_result
            
            # Log cleanup summary
            if cleanup_result['cleanup_attempted']:
                self.logger.info(f"Source cleanup summary: {cleanup_result['cleaned_files']} files deleted, "
                               f"{cleanup_result['failed_cleanups']} failures")
            else:
                self.logger.warning(f"Source cleanup was not performed: {cleanup_result.get('reason', 'Unknown reason')}")
        else:
            self.logger.info("Source file cleanup was not requested")
            translation_result['source_cleanup'] = {
                'cleanup_attempted': False,
                'reason': 'Cleanup not requested',
                'cleaned_files': 0,
                'failed_cleanups': 0,
                'errors': []
            }
        
        return translation_result

    def translate_documents_default(
        self,
        target_language: str,
        source_language: Optional[str] = None,
        clear_target: bool = True,
        cleanup_source: bool = False,
        cleanup_old_target_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Convenience method to translate documents using default source and target URIs from configuration.
        
        Args:
            target_language (str): Target language code (e.g., 'en', 'es', 'fr')
            source_language (str, optional): Source language code. If not provided, auto-detection is used.
            clear_target (bool, optional): Whether to clear target container before translation. Defaults to True.
            cleanup_source (bool, optional): Whether to clean up source files after translation. Defaults to False.
            cleanup_old_target_hours (int, optional): Hours to keep old target files before cleanup. Defaults to 24.
        
        Returns:
            Dict[str, Any]: Translation results including status, document details, and cleanup information
        
        Raises:
            ValueError: If configuration is invalid
            Exception: If translation operation fails
        """
        try:
            # Get default URIs from configuration
            config = get_config()
            source_uri = config.source_uri
            target_uri = config.target_uri
            
            self.logger.info(f"Using default source URI: {source_uri}")
            self.logger.info(f"Using default target URI: {target_uri}")
            
            # Call the full method with default URIs
            return self.translate_documents_with_cleanup(
                source_uri=source_uri,
                target_uri=target_uri,
                target_language=target_language,
                source_language=source_language,
                clear_target=clear_target,
                cleanup_source=cleanup_source,
                cleanup_old_target_hours=cleanup_old_target_hours
            )
            
        except ValueError as e:
            self.logger.error(f"Configuration error in translate_documents: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Translation error in translate_documents: {str(e)}")
            raise Exception(f"Document translation failed: {str(e)}")

    def _extract_filename_from_url(self, url: Optional[str]) -> Optional[str]:
        """
        Extract filename from a blob storage URL.
        
        Args:
            url (str, optional): The blob storage URL
        
        Returns:
            str, optional: The filename if extractable, None otherwise
        """
        if not url:
            return None
        
        try:
            # URL format: https://account.blob.core.windows.net/container/filename
            # Extract the last part after the final '/'
            filename = url.split('/')[-1]
            
            # Remove any query parameters
            if '?' in filename:
                filename = filename.split('?')[0]
            
            # Decode URL encoding if present
            import urllib.parse
            filename = urllib.parse.unquote(filename)
            
            # Log the extraction for debugging
            self.logger.debug(f"Extracted filename '{filename}' from URL: {url}")
            
            return filename if filename else None
        except Exception as e:
            self.logger.warning(f"Failed to extract filename from URL {url}: {str(e)}")
            return None

    def cleanup_target_file(self, target_uri: str, filename: str) -> Dict[str, Any]:
        """
        Clean up a specific translated file from the target container.
        
        Args:
            target_uri (str): URI of the target blob container
            filename (str): Name of the file to delete
        
        Returns:
            Dict[str, Any]: Cleanup result including success status and details
        """
        if not self.blob_service_client:
            self.logger.warning("Blob service client not available - skipping target file cleanup")
            return {
                'success': False,
                'reason': 'Blob service client not available',
                'filename': filename
            }
        
        try:
            # Extract container name from URI
            uri_parts = target_uri.rstrip('/').split('/')
            if len(uri_parts) < 4:
                self.logger.error(f"Invalid target URI format: {target_uri}")
                return {
                    'success': False,
                    'reason': f'Invalid target URI format: {target_uri}',
                    'filename': filename
                }
            
            container_name = uri_parts[-1]
            self.logger.info(f"Attempting to delete target file: {filename} from container: {container_name}")
            
            # Get blob client for the specific file
            blob_client = self.blob_service_client.get_blob_client(container=container_name, blob=filename)
            
            # Check if blob exists before attempting deletion
            if blob_client.exists():
                # Delete the target file
                blob_client.delete_blob()
                self.logger.info(f"Successfully deleted target file: {filename}")
                return {
                    'success': True,
                    'filename': filename,
                    'container_name': container_name
                }
            else:
                self.logger.info(f"Target file {filename} was already deleted or doesn't exist")
                return {
                    'success': True,
                    'reason': 'File already deleted or does not exist',
                    'filename': filename,
                    'container_name': container_name
                }
                
        except ResourceNotFoundError:
            # File was already deleted, this is considered success
            self.logger.info(f"Target file {filename} was already deleted")
            return {
                'success': True,
                'reason': 'File was already deleted',
                'filename': filename
            }
        except Exception as e:
            error_msg = f"Failed to delete target file {filename}: {str(e)}"
            self.logger.error(error_msg)
            return {
                'success': False,
                'reason': error_msg,
                'filename': filename
            }

    def cleanup_target_files(self, target_uri: str, filenames: List[str]) -> Dict[str, Any]:
        """
        Clean up multiple translated files from the target container.
        
        Args:
            target_uri (str): URI of the target blob container
            filenames (List[str]): List of filenames to delete
        
        Returns:
            Dict[str, Any]: Cleanup results including success/failure counts
        """
        if not filenames:
            return {
                'cleanup_attempted': False,
                'reason': 'No filenames provided',
                'cleaned_files': 0,
                'failed_cleanups': 0,
                'results': []
            }
        
        cleaned_files = 0
        failed_cleanups = 0
        results = []
        
        for filename in filenames:
            result = self.cleanup_target_file(target_uri, filename)
            results.append(result)
            
            if result['success']:
                cleaned_files += 1
            else:
                failed_cleanups += 1
        
        cleanup_result = {
            'cleanup_attempted': True,
            'cleaned_files': cleaned_files,
            'failed_cleanups': failed_cleanups,
            'results': results
        }
        
        self.logger.info(f"Target cleanup completed: {cleaned_files} files deleted, {failed_cleanups} failures")
        return cleanup_result

    def cleanup_old_target_files(self, target_uri: str, hours_threshold: int = 72) -> Dict[str, Any]:
        """
        Clean up old translated files from the target container that are older than the specified threshold.
        
        Args:
            target_uri (str): URI of the target blob container
            hours_threshold (int, optional): Age threshold in hours. Files older than this will be deleted. Defaults to 72 hours (3 days).
        
        Returns:
            Dict[str, Any]: Cleanup results including success/failure counts and details
        """
        if not self.blob_service_client:
            self.logger.warning("Blob service client not available - skipping old target files cleanup")
            return {
                'cleanup_attempted': False,
                'reason': 'Blob service client not available',
                'cleaned_files': 0,
                'failed_cleanups': 0,
                'old_files_found': 0,
                'errors': []
            }
        
        try:
            # Extract container name from URI
            uri_parts = target_uri.rstrip('/').split('/')
            if len(uri_parts) < 4:
                self.logger.error(f"Invalid target URI format: {target_uri}")
                return {
                    'cleanup_attempted': False,
                    'reason': f'Invalid target URI format: {target_uri}',
                    'cleaned_files': 0,
                    'failed_cleanups': 0,
                    'old_files_found': 0,
                    'errors': []
                }
            
            container_name = uri_parts[-1]
            self.logger.info(f"Starting cleanup of old files in target container: {container_name}")
            self.logger.info(f"Deleting files older than {hours_threshold} hours ({hours_threshold/24:.1f} days)")
            
            # Calculate the cutoff time (current time - threshold hours)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)
            self.logger.info(f"Cutoff time for cleanup: {cutoff_time.isoformat()}")
            
            # Get container client
            container_client = self.blob_service_client.get_container_client(container_name)
            
            # Check if container exists
            try:
                container_client.get_container_properties()
            except ResourceNotFoundError:
                self.logger.info(f"Target container {container_name} does not exist - no cleanup needed")
                return {
                    'cleanup_attempted': True,
                    'reason': 'Container does not exist',
                    'cleaned_files': 0,
                    'failed_cleanups': 0,
                    'old_files_found': 0,
                    'errors': []
                }
            
            cleaned_files = 0
            failed_cleanups = 0
            old_files_found = 0
            cleanup_errors = []
            
            # List all blobs in the container with their properties
            self.logger.info("Scanning target container for old files...")
            blob_list = container_client.list_blobs(include=['metadata'])
            
            for blob in blob_list:
                try:
                    # Get the blob's last modified time
                    last_modified = blob.last_modified
                    
                    # Ensure last_modified is timezone-aware
                    if last_modified.tzinfo is None:
                        last_modified = last_modified.replace(tzinfo=timezone.utc)
                    
                    # Check if the file is older than the threshold
                    if last_modified < cutoff_time:
                        old_files_found += 1
                        age_hours = (datetime.now(timezone.utc) - last_modified).total_seconds() / 3600
                        self.logger.info(f"Found old file: {blob.name} (age: {age_hours:.1f} hours)")
                        
                        try:
                            # Delete the old file
                            blob_client = container_client.get_blob_client(blob.name)
                            blob_client.delete_blob()
                            cleaned_files += 1
                            self.logger.info(f"Successfully deleted old target file: {blob.name}")
                        except Exception as delete_error:
                            failed_cleanups += 1
                            error_msg = f"Failed to delete old target file {blob.name}: {str(delete_error)}"
                            cleanup_errors.append(error_msg)
                            self.logger.error(error_msg)
                    else:
                        # File is recent, keep it
                        age_hours = (datetime.now(timezone.utc) - last_modified).total_seconds() / 3600
                        self.logger.debug(f"Keeping recent file: {blob.name} (age: {age_hours:.1f} hours)")
                        
                except Exception as e:
                    error_msg = f"Error processing blob {blob.name}: {str(e)}"
                    cleanup_errors.append(error_msg)
                    self.logger.error(error_msg)
            
            cleanup_result = {
                'cleanup_attempted': True,
                'cleaned_files': cleaned_files,
                'failed_cleanups': failed_cleanups,
                'old_files_found': old_files_found,
                'hours_threshold': hours_threshold,
                'cutoff_time': cutoff_time.isoformat(),
                'container_name': container_name,
                'errors': cleanup_errors
            }
            
            if old_files_found > 0:
                self.logger.info(f"Old target files cleanup completed: {cleaned_files} files deleted, {failed_cleanups} failures, {old_files_found} old files found")
            else:
                self.logger.info("No old target files found - cleanup not needed")
            
            return cleanup_result
            
        except Exception as e:
            error_msg = f"Failed to cleanup old target files: {str(e)}"
            self.logger.error(error_msg)
            return {
                'cleanup_attempted': False,
                'reason': error_msg,
                'cleaned_files': 0,
                'failed_cleanups': 0,                'old_files_found': 0,
                'errors': [error_msg]
            }

    def translate_documents_with_cleanup_for_user(
        self, 
        source_uri: str, 
        target_uri: str, 
        target_language: str,
        user_id_hash: str,
        source_language: Optional[str] = None,
        clear_target: bool = True,
        cleanup_source: bool = False,
        cleanup_old_target_hours: int = 24
    ) -> Dict[str, Any]:
        """
        Translate documents for a specific user with container-level access but user isolation.
        
        Args:
            source_uri (str): URI of the source blob container (container level)
            target_uri (str): URI of the target blob container (container level)
            target_language (str): Target language code (e.g., 'en', 'es', 'fr')
            user_id_hash (str): User ID hash for filtering and isolation
            source_language (str, optional): Source language code. If not provided, auto-detection is used.
            clear_target (bool, optional): Whether to clear user's target files before translation. Defaults to True.
            cleanup_source (bool, optional): Whether to clean up user's source files after translation. Defaults to False.
            cleanup_old_target_hours (int, optional): Hours threshold for cleaning up old target files. Defaults to 24 hours.
        
        Returns:
            Dict[str, Any]: Translation results including cleanup information
        """
        self.logger.info(f"Starting user-specific translation for user hash: {user_id_hash}")
        
        # First, clean up old target files for this user
        old_target_cleanup_result = self.cleanup_old_target_files_for_user(target_uri, user_id_hash, cleanup_old_target_hours)
        
        # Clear user's target files if requested
        if clear_target:
            self.logger.info(f"Clearing target files for user: {user_id_hash}")
            user_target_cleanup_result = self._clear_user_target_files(target_uri, user_id_hash)
        
        # Check if user has any source files to translate
        if not self._user_has_source_files(source_uri, user_id_hash):
            return {
                'status': 'No files to translate',
                'success': False,
                'error': 'No source files found for the current user',
                'user_id_hash': user_id_hash,
                'old_target_cleanup': old_target_cleanup_result,
                'source_files_found': 0
            }
        
        # Create user-specific source and target URIs with SAS tokens if needed
        # The translation service needs container-level access, but we can use filters
        try:
            # Use the entire container for translation (Azure Document Translation needs this)
            # But the service will translate ALL files in the container
            self.logger.info(f"Translating documents in container with user filtering")
            
            # Perform the actual translation using the base method
            result = self.translate_documents(
                source_uri=source_uri,
                target_uri=target_uri,
                target_language=target_language,
                source_language=source_language,
                clear_target=False  # We already handled user-specific clearing
            )
            
            # Filter the results to only include this user's files
            if 'documents' in result:
                user_documents = []
                for doc in result['documents']:
                    # Check if this document belongs to the user
                    source_url = doc.get('source_url', '')
                    if user_id_hash in source_url or self._is_user_document(source_url, user_id_hash):
                        user_documents.append(doc)
                
                result['documents'] = user_documents
                result['user_documents_count'] = len(user_documents)
                result['total_documents_in_container'] = len(result.get('all_documents', []))
            
            # Add user-specific cleanup information
            result['user_id_hash'] = user_id_hash
            result['old_target_cleanup'] = old_target_cleanup_result
            result['cleanup_source_requested'] = cleanup_source
            
            # Clean up user's source files if requested and translation was successful
            if cleanup_source and result.get('status') == 'Succeeded':
                self.logger.info(f"Cleaning up source files for user: {user_id_hash}")
                source_cleanup_result = self.cleanup_source_files_for_user(source_uri, user_id_hash)
                result['source_cleanup'] = source_cleanup_result
            else:
                result['source_cleanup'] = {'cleanup_attempted': False, 'reason': 'Translation not successful or cleanup not requested'}
            
            return result
            
        except Exception as e:
            self.logger.error(f"Translation failed for user {user_id_hash}: {str(e)}")
            return {
                'status': 'Failed',
                'success': False,
                'error': str(e),
                'user_id_hash': user_id_hash,
                'old_target_cleanup': old_target_cleanup_result
            }

    def _user_has_source_files(self, source_uri: str, user_id_hash: str) -> bool:
        """Check if user has any source files to translate."""
        if not self.blob_service_client:
            return False
        
        try:
            # Extract container name from URI
            container_name = self._extract_container_name_from_uri(source_uri)
            if not container_name:
                return False
            
            container_client = self.blob_service_client.get_container_client(container_name)
            
            # Check if any blobs exist with the user's prefix
            blob_list = container_client.list_blobs(name_starts_with=f"{user_id_hash}/")
            
            # Check if there are any blobs
            for blob in blob_list:
                self.logger.info(f"Found source file for user {user_id_hash}: {blob.name}")
                return True
            
            self.logger.info(f"No source files found for user {user_id_hash}")
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking user source files: {str(e)}")
            return False

    def _clear_user_target_files(self, target_uri: str, user_id_hash: str) -> Dict[str, Any]:
        """Clear target files for a specific user."""
        if not self.blob_service_client:
            return {'cleanup_attempted': False, 'error': 'No blob service client'}
        
        try:
            container_name = self._extract_container_name_from_uri(target_uri)
            if not container_name:
                return {'cleanup_attempted': False, 'error': 'Could not extract container name'}
            
            container_client = self.blob_service_client.get_container_client(container_name)
            
            # List and delete blobs with user prefix
            blob_list = container_client.list_blobs(name_starts_with=f"{user_id_hash}/")
            deleted_count = 0
            
            for blob in blob_list:
                try:
                    container_client.delete_blob(blob.name)
                    deleted_count += 1
                    self.logger.info(f"Deleted user target file: {blob.name}")
                except Exception as e:
                    self.logger.error(f"Failed to delete target file {blob.name}: {str(e)}")
            
            return {
                'cleanup_attempted': True,
                'deleted_count': deleted_count,
                'user_id_hash': user_id_hash
            }
            
        except Exception as e:
            self.logger.error(f"Error clearing user target files: {str(e)}")
            return {'cleanup_attempted': False, 'error': str(e)}

    def cleanup_source_files_for_user(self, source_uri: str, user_id_hash: str) -> Dict[str, Any]:
        """Clean up source files for a specific user."""
        if not self.blob_service_client:
            return {'cleanup_attempted': False, 'error': 'No blob service client'}
        
        try:
            container_name = self._extract_container_name_from_uri(source_uri)
            if not container_name:
                return {'cleanup_attempted': False, 'error': 'Could not extract container name'}
            
            container_client = self.blob_service_client.get_container_client(container_name)
            
            # List and delete blobs with user prefix
            blob_list = container_client.list_blobs(name_starts_with=f"{user_id_hash}/")
            deleted_count = 0
            failed_count = 0
            
            for blob in blob_list:
                try:
                    container_client.delete_blob(blob.name)
                    deleted_count += 1
                    self.logger.info(f"Deleted user source file: {blob.name}")
                except Exception as e:
                    failed_count += 1
                    self.logger.error(f"Failed to delete source file {blob.name}: {str(e)}")
            
            return {
                'cleanup_attempted': True,
                'cleaned_files': deleted_count,
                'failed_cleanups': failed_count,
                'user_id_hash': user_id_hash
            }
            
        except Exception as e:
            self.logger.error(f"Error cleaning up user source files: {str(e)}")
            return {'cleanup_attempted': False, 'error': str(e)}

    def cleanup_old_target_files_for_user(self, target_uri: str, user_id_hash: str, hours_threshold: int = 72) -> Dict[str, Any]:
        """Clean up old target files for a specific user."""
        if not self.blob_service_client:
            return {'cleanup_attempted': False, 'error': 'No blob service client'}
        
        try:
            container_name = self._extract_container_name_from_uri(target_uri)
            if not container_name:
                return {'cleanup_attempted': False, 'error': 'Could not extract container name'}
            
            container_client = self.blob_service_client.get_container_client(container_name)
            cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours_threshold)
            
            # List blobs with user prefix and check age
            blob_list = container_client.list_blobs(name_starts_with=f"{user_id_hash}/", include=['metadata'])
            old_files_found = 0
            cleaned_files = 0
            failed_cleanups = 0
            
            for blob in blob_list:
                if blob.last_modified and blob.last_modified < cutoff_time:
                    old_files_found += 1
                    try:
                        container_client.delete_blob(blob.name)
                        cleaned_files += 1
                        self.logger.info(f"Deleted old target file: {blob.name}")
                    except Exception as e:
                        failed_cleanups += 1
                        self.logger.error(f"Failed to delete old target file {blob.name}: {str(e)}")
            
            return {
                'cleanup_attempted': True,
                'old_files_found': old_files_found,
                'cleaned_files': cleaned_files,
                'failed_cleanups': failed_cleanups,
                'hours_threshold': hours_threshold,
                'user_id_hash': user_id_hash
            }
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old target files for user: {str(e)}")
            return {'cleanup_attempted': False, 'error': str(e)}

    def _is_user_document(self, source_url: str, user_id_hash: str) -> bool:
        """Check if a document belongs to the specified user."""
        # Extract blob name from URL and check if it starts with user hash
        try:
            # Parse the URL to get the blob name
            from urllib.parse import urlparse
            parsed = urlparse(source_url)
            # The blob name is everything after the container name in the path
            path_parts = parsed.path.strip('/').split('/')
            if len(path_parts) >= 2:
                blob_name = '/'.join(path_parts[1:])  # Skip container name
                return blob_name.startswith(f"{user_id_hash}/")
            return False
        except Exception as e:
            self.logger.error(f"Error checking if document belongs to user: {str(e)}")
            return False

    def _extract_container_name_from_uri(self, uri: str) -> Optional[str]:
        """Extract container name from a blob storage URI."""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(uri)
            path_parts = parsed.path.strip('/').split('/')
            if path_parts:
                return path_parts[0]
            return None
        except Exception as e:
            self.logger.error(f"Error extracting container name from URI: {str(e)}")
            return None

    def translate_user_documents_with_temp_containers(
        self,
        original_source_uri: str,
        original_target_uri: str,
        temp_source_uri: str,
        temp_target_uri: str,
        target_language: str,
        user_id_hash: str,
        source_language: Optional[str] = None,
        cleanup_source: bool = False
    ) -> Dict[str, Any]:
        """
        Translate user documents using temporary containers for isolation.        
        This method:
        1. Creates temporary containers
        2. Copies user's files to temp source container
        3. Performs translation from temp source to temp target
        4. Copies translated files back to user's path in main target container
        5. Cleans up temporary containers
        
        Args:
            original_source_uri (str): URI of the main source container
            original_target_uri (str): URI of the main target container
            temp_source_uri (str): URI for temporary source container
            temp_target_uri (str): URI for temporary target container
            target_language (str): Target language code
            user_id_hash (str): User ID hash for filtering
            source_language (str, optional): Source language code
            cleanup_source (bool, optional): Whether to clean up original source files. Defaults to False.
        
        Returns:
            Dict[str, Any]: Translation results
        """
        temp_source_container = None
        temp_target_container = None
        
        try:
            if not self.blob_service_client:
                raise Exception("Blob service client not available")
            
            # Extract container names
            temp_source_container = self._extract_container_name_from_uri(temp_source_uri)
            temp_target_container = self._extract_container_name_from_uri(temp_target_uri)
            original_source_container = self._extract_container_name_from_uri(original_source_uri)
            original_target_container = self._extract_container_name_from_uri(original_target_uri)
            
            self.logger.info(f"Creating temporary containers for user {user_id_hash}")
            self.logger.info(f"Temp source: {temp_source_container}, Temp target: {temp_target_container}")
            
            # Step 1: Create temporary containers
            self._create_container_if_not_exists(temp_source_container)
            self._create_container_if_not_exists(temp_target_container)
            
            # Step 2: Copy user's files to temporary source container
            copied_files = self._copy_user_files_to_temp_container(
                original_source_container, temp_source_container, user_id_hash
            )
            
            if copied_files == 0:
                self.logger.warning(f"No files found for user {user_id_hash}")
                return {
                    'status': 'No files to translate',
                    'success': False,
                    'error': 'No source files found for the current user',
                    'user_id_hash': user_id_hash,
                    'copied_files': 0
                }
            
            self.logger.info(f"Copied {copied_files} files for translation")
            
            # Step 3: Perform translation using temporary containers
            translation_result = self.translate_documents(
                source_uri=temp_source_uri,
                target_uri=temp_target_uri,
                target_language=target_language,
                source_language=source_language,
                clear_target=True
            )
            
            # Step 4: Copy translated files back to main target container with user prefix
            if translation_result.get('status') == 'Succeeded':
                moved_files = self._move_translated_files_to_user_path(
                    temp_target_container, original_target_container, user_id_hash
                )
                translation_result['moved_files'] = moved_files
                self.logger.info(f"Moved {moved_files} translated files back to main container")
                
                # Step 5: Clean up source files if requested
                if cleanup_source:
                    source_cleanup = self._cleanup_user_source_files(original_source_container, user_id_hash)
                    translation_result['source_cleanup'] = source_cleanup
            
            # Add user-specific information
            translation_result['user_id_hash'] = user_id_hash
            translation_result['copied_files'] = copied_files
            translation_result['temp_containers_used'] = True
            
            return translation_result
            
        except Exception as e:
            self.logger.error(f"Translation with temp containers failed: {str(e)}")
            return {
                'status': 'Failed',
                'success': False,
                'error': str(e),
                'user_id_hash': user_id_hash,
                'temp_containers_used': True
            }
        finally:
            # Always clean up temporary containers
            self._cleanup_temp_containers(temp_source_container, temp_target_container)

    def _create_container_if_not_exists(self, container_name: str) -> bool:
        """Create a container if it doesn't exist."""
        try:
            container_client = self.blob_service_client.get_container_client(container_name)
            container_client.create_container()
            self.logger.info(f"Created temporary container: {container_name}")
            return True
        except Exception as e:
            if "ContainerAlreadyExists" in str(e):
                self.logger.info(f"Container {container_name} already exists")
                return True
            else:
                self.logger.error(f"Failed to create container {container_name}: {str(e)}")
                return False

    def _copy_user_files_to_temp_container(self, source_container: str, temp_container: str, user_id_hash: str) -> int:
        """Copy user's files from main container to temporary container."""
        try:
            source_client = self.blob_service_client.get_container_client(source_container)
            temp_client = self.blob_service_client.get_container_client(temp_container)
            
            # List user's blobs
            user_blobs = source_client.list_blobs(name_starts_with=f"{user_id_hash}/")
            copied_count = 0
            
            for blob in user_blobs:
                # Copy blob to temp container without the user prefix
                # Original: user_hash/filename.pdf -> Temp: filename.pdf
                filename = blob.name.replace(f"{user_id_hash}/", "")
                
                # Get source blob client
                source_blob_client = source_client.get_blob_client(blob.name)
                
                # Get temp blob client
                temp_blob_client = temp_client.get_blob_client(filename)
                
                # Copy the blob
                copy_source = source_blob_client.url
                temp_blob_client.start_copy_from_url(copy_source)
                
                copied_count += 1
                self.logger.info(f"Copied {blob.name} -> {filename}")
            
            return copied_count
            
        except Exception as e:
            self.logger.error(f"Error copying user files to temp container: {str(e)}")
            return 0

    def _move_translated_files_to_user_path(self, temp_container: str, target_container: str, user_id_hash: str) -> int:
        """Move translated files from temp container to main target container with user prefix."""
        try:
            temp_client = self.blob_service_client.get_container_client(temp_container)
            target_client = self.blob_service_client.get_container_client(target_container)
            
            # List all blobs in temp target container
            temp_blobs = temp_client.list_blobs()
            moved_count = 0
            
            for blob in temp_blobs:
                # Move blob to target container with user prefix
                # Temp: filename.pdf -> Target: user_hash/filename.pdf
                target_blob_name = f"{user_id_hash}/{blob.name}"
                
                # Get temp blob client
                temp_blob_client = temp_client.get_blob_client(blob.name)
                
                # Get target blob client
                target_blob_client = target_client.get_blob_client(target_blob_name)
                
                # Copy the blob
                copy_source = temp_blob_client.url
                target_blob_client.start_copy_from_url(copy_source)
                
                moved_count += 1
                self.logger.info(f"Moved {blob.name} -> {target_blob_name}")
            
            return moved_count
            
        except Exception as e:
            self.logger.error(f"Error moving translated files: {str(e)}")
            return 0

    def _cleanup_user_source_files(self, source_container: str, user_id_hash: str) -> Dict[str, Any]:
        """Clean up user's source files after successful translation."""
        try:
            container_client = self.blob_service_client.get_container_client(source_container)
            
            # List and delete user's blobs
            user_blobs = container_client.list_blobs(name_starts_with=f"{user_id_hash}/")
            deleted_count = 0
            failed_count = 0
            
            for blob in user_blobs:
                try:
                    container_client.delete_blob(blob.name)
                    deleted_count += 1
                    self.logger.info(f"Deleted source file: {blob.name}")
                except Exception as e:
                    failed_count += 1
                    self.logger.error(f"Failed to delete source file {blob.name}: {str(e)}")
            
            return {
                'cleanup_attempted': True,
                'cleaned_files': deleted_count,
                'failed_cleanups': failed_count,
                'user_id_hash': user_id_hash
            }
            
        except Exception as e:
            self.logger.error(f"Error cleaning up user source files: {str(e)}")
            return {'cleanup_attempted': False, 'error': str(e)}

    def _cleanup_temp_containers(self, temp_source_container: str, temp_target_container: str):
        """Clean up temporary containers."""
        containers_to_cleanup = [temp_source_container, temp_target_container]
        
        for container_name in containers_to_cleanup:
            if container_name:
                try:
                    container_client = self.blob_service_client.get_container_client(container_name)
                    container_client.delete_container()
                    self.logger.info(f"Deleted temporary container: {container_name}")
                except Exception as e:
                    self.logger.warning(f"Failed to delete temporary container {container_name}: {str(e)}")

    # ...existing code...

def create_translation_service(key: Optional[str] = None, endpoint: Optional[str] = None) -> DocumentTranslationService:
    """
    Factory function to create a DocumentTranslationService instance.
    
    Args:
        key (str, optional): Azure Cognitive Services API key. If not provided, will use config.
        endpoint (str, optional): Azure Cognitive Services endpoint URL. If not provided, will use config.
    
    Returns:
        DocumentTranslationService: Configured translation service instance
    """
    config = get_config()
    actual_key = key or config.key
    actual_endpoint = endpoint or config.endpoint
    return DocumentTranslationService(actual_key, actual_endpoint)


# Convenience function for backward compatibility with the original script
def translate_documents_simple(
    source_uri: str, 
    target_uri: str, 
    target_language: str,
    key: Optional[str] = None,
    endpoint: Optional[str] = None,
    clear_target: bool = True
) -> Dict[str, Any]:
    """
    Simple function to translate documents (backward compatibility).
    
    Args:
        source_uri (str): URI of the source blob container
        target_uri (str): URI of the target blob container
        target_language (str): Target language code
        key (str, optional): Azure Cognitive Services API key. If not provided, will use config.
        endpoint (str, optional): Azure Cognitive Services endpoint URL. If not provided, will use config.
        clear_target (bool, optional): Whether to clear target container before translation. Defaults to True.
    
    Returns:
        Dict[str, Any]: Translation results
    """
    service = create_translation_service(key, endpoint)
    return service.translate_documents(source_uri, target_uri, target_language, clear_target=clear_target)

# Convenience function for translation with source cleanup
def translate_documents_with_cleanup(
    source_uri: str, 
    target_uri: str, 
    target_language: str,
    source_language: Optional[str] = None,
    key: Optional[str] = None,
    endpoint: Optional[str] = None,
    clear_target: bool = True,
    cleanup_source: bool = False,
    cleanup_old_target_hours: int = 24
) -> Dict[str, Any]:
    """
    Simple function to translate documents with optional source cleanup and automatic old target files cleanup.
    
    Args:
        source_uri (str): URI of the source blob container
        target_uri (str): URI of the target blob container
        target_language (str): Target language code
        source_language (str, optional): Source language code. If not provided, auto-detection is used.
        key (str, optional): Azure Cognitive Services API key. If not provided, will use config.
        endpoint (str, optional): Azure Cognitive Services endpoint URL. If not provided, will use config.
        clear_target (bool, optional): Whether to clear target container before translation. Defaults to True.
        cleanup_source (bool, optional): Whether to clean up source files after translation. Defaults to False.
        cleanup_old_target_hours (int, optional): Hours threshold for cleaning up old target files. Defaults to 24 hours (1 day).
    
    Returns:
        Dict[str, Any]: Translation results including cleanup information
    """
    service = create_translation_service(key, endpoint)
    return service.translate_documents_with_cleanup(
        source_uri=source_uri, 
        target_uri=target_uri, 
        target_language=target_language,
        source_language=source_language,
        clear_target=clear_target,
        cleanup_source=cleanup_source,
        cleanup_old_target_hours=cleanup_old_target_hours
    )

# Convenience function for user-specific translation
def translate_documents_with_cleanup_for_user(
    source_uri: str, 
    target_uri: str, 
    target_language: str,
    user_id_hash: str,
    source_language: Optional[str] = None,
    key: Optional[str] = None,
    endpoint: Optional[str] = None,
    clear_target: bool = True,
    cleanup_source: bool = False,
    cleanup_old_target_hours: int = 24
) -> Dict[str, Any]:
    """
    Simple function to translate documents for a specific user with user isolation.
    
    Args:
        source_uri (str): URI of the source blob container
        target_uri (str): URI of the target blob container
        target_language (str): Target language code
        user_id_hash (str): User ID hash for filtering and isolation
        source_language (str, optional): Source language code. If not provided, auto-detection is used.
        key (str, optional): Azure Cognitive Services API key. If not provided, will use config.
        endpoint (str, optional): Azure Cognitive Services endpoint URL. If not provided, will use config.
        clear_target (bool, optional): Whether to clear user's target files before translation. Defaults to True.
        cleanup_source (bool, optional): Whether to clean up user's source files after translation. Defaults to False.
        cleanup_old_target_hours (int, optional): Hours threshold for cleaning up old target files. Defaults to 24 hours.
    
    Returns:
        Dict[str, Any]: Translation results including cleanup information
    """
    service = create_translation_service(key, endpoint)
    return service.translate_documents_with_cleanup_for_user(
        source_uri=source_uri, 
        target_uri=target_uri, 
        target_language=target_language,
        user_id_hash=user_id_hash,
        source_language=source_language,
        clear_target=clear_target,
        cleanup_source=cleanup_source,
        cleanup_old_target_hours=cleanup_old_target_hours
    )
