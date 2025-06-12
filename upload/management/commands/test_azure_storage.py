from django.core.management.base import BaseCommand
from azure.storage.blob import BlobServiceClient
from azure.core.exceptions import AzureError
import os
import urllib.parse


class Command(BaseCommand):
    help = 'Test Azure Storage connection and validate configuration'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-encoding',
            action='store_true',
            help='Attempt to fix URL encoding issues in connection string',
        )

    def handle(self, *args, **options):
        self.stdout.write('🔍 Testing Azure Storage Configuration...\n')
        
        # Get connection string
        connection_string = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
        
        if not connection_string:
            self.stdout.write(
                self.style.ERROR('❌ AZURE_STORAGE_CONNECTION_STRING not found in environment variables')
            )
            self.stdout.write('Please set this environment variable or add it to your .env file.')
            return
        
        # Check for URL encoding issues
        if '%' in connection_string:
            self.stdout.write(
                self.style.WARNING(f'⚠️  Connection string contains URL encoding: {connection_string[:50]}...')
            )
            
            if options['fix_encoding']:
                try:
                    decoded = urllib.parse.unquote(connection_string)
                    self.stdout.write(self.style.SUCCESS('✅ Decoded URL-encoded connection string'))
                    connection_string = decoded
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'❌ Failed to decode: {e}'))
                    return
            else:
                self.stdout.write('Run with --fix-encoding to attempt automatic fix.')
                return
        
        # Validate connection string format
        required_parts = ['DefaultEndpointsProtocol', 'AccountName', 'AccountKey']
        missing_parts = [part for part in required_parts if part not in connection_string]
        
        if missing_parts:
            self.stdout.write(
                self.style.ERROR(f'❌ Connection string missing required parts: {missing_parts}')
            )
            self.stdout.write('Expected format: DefaultEndpointsProtocol=https;AccountName=...;AccountKey=...;EndpointSuffix=core.windows.net')
            return
        
        self.stdout.write(self.style.SUCCESS('✅ Connection string format appears valid'))
        
        # Test actual connection
        try:
            self.stdout.write('🔗 Testing connection to Azure Storage...')
            blob_service_client = BlobServiceClient.from_connection_string(connection_string)
            
            # Try to list containers
            containers = list(blob_service_client.list_containers(results_per_page=5))
            
            self.stdout.write(self.style.SUCCESS('✅ Successfully connected to Azure Storage'))
            self.stdout.write(f'📦 Found {len(containers)} containers:')
            
            for container in containers:
                self.stdout.write(f'   - {container.name}')
            
            # Test container creation (if needed)
            source_container = os.getenv('AZURE_STORAGE_CONTAINER_NAME_SOURCE', 'source')
            target_container = os.getenv('AZURE_STORAGE_CONTAINER_NAME_TARGET', 'target')
            
            self.stdout.write(f'\n📋 Checking required containers:')
            
            for container_name in [source_container, target_container]:
                try:
                    container_client = blob_service_client.get_container_client(container_name)
                    container_client.get_container_properties()
                    self.stdout.write(self.style.SUCCESS(f'   ✅ {container_name} exists'))
                except Exception:
                    self.stdout.write(self.style.WARNING(f'   ⚠️  {container_name} does not exist (will be created on first upload)'))
            
            # Test translation service configuration
            self.stdout.write(f'\n🌐 Checking Translation Service configuration:')
            
            translation_key = os.getenv('AZURE_TRANSLATION_KEY')
            translation_endpoint = os.getenv('AZURE_TRANSLATION_ENDPOINT')
            
            if translation_key and translation_key != 'your-translation-key':
                self.stdout.write(self.style.SUCCESS('   ✅ AZURE_TRANSLATION_KEY configured'))
            else:
                self.stdout.write(self.style.WARNING('   ⚠️  AZURE_TRANSLATION_KEY not configured'))
            
            if translation_endpoint and translation_endpoint != 'your-translation-endpoint':
                self.stdout.write(self.style.SUCCESS('   ✅ AZURE_TRANSLATION_ENDPOINT configured'))
            else:
                self.stdout.write(self.style.WARNING('   ⚠️  AZURE_TRANSLATION_ENDPOINT not configured'))
            
            self.stdout.write(self.style.SUCCESS('\n🎉 Azure Storage test completed successfully!'))
            
        except AzureError as e:
            self.stdout.write(self.style.ERROR(f'❌ Azure Storage connection failed: {e}'))
            self.stdout.write('Please check your connection string and ensure the storage account is accessible.')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Unexpected error: {e}'))
