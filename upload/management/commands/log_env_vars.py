import os
import logging
from django.core.management.base import BaseCommand
from django.conf import settings

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Log environment variables for debugging (Azure-focused)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--azure-only',
            action='store_true',
            help='Show only Azure-related environment variables',
        )

    def handle(self, *args, **options):
        if options['azure_only'] or not settings.DEBUG:
            # Show Azure-related variables regardless of DEBUG mode
            self.stdout.write(self.style.SUCCESS('=== AZURE ENVIRONMENT VARIABLES ==='))
            
            azure_vars = [
                'AZURE_STORAGE_CONNECTION_STRING',
                'AZURE_STORAGE_CONTAINER_NAME_SOURCE',
                'AZURE_STORAGE_CONTAINER_NAME_TARGET',
                'AZURE_TRANSLATION_KEY',
                'AZURE_TRANSLATION_ENDPOINT',
                'AZURE_TRANSLATION_SOURCE_URI',
                'AZURE_TRANSLATION_TARGET_URI'
            ]
            
            for var in azure_vars:
                value = os.getenv(var)
                if value:
                    # Mask sensitive values but show length and partial content
                    if 'CONNECTION_STRING' in var or 'KEY' in var:
                        if len(value) > 20:
                            masked_value = f"{value[:10]}...{value[-4:]} (length: {len(value)})"
                        else:
                            masked_value = '*' * len(value)
                    else:
                        masked_value = value
                    
                    self.stdout.write(f"✅ {var}={masked_value}")
                else:
                    self.stdout.write(self.style.WARNING(f"❌ {var}=<not set>"))
            
            self.stdout.write(self.style.SUCCESS('=== END AZURE ENVIRONMENT VARIABLES ==='))
            
        elif settings.DEBUG:
            self.stdout.write(self.style.SUCCESS('=== ALL ENVIRONMENT VARIABLES ==='))
            
            # Sort environment variables for better readability
            sorted_env = dict(sorted(os.environ.items()))
            
            for key, value in sorted_env.items():
                # Mask sensitive values
                if any(sensitive in key.upper() for sensitive in ['SECRET', 'KEY', 'PASSWORD', 'TOKEN', 'CONNECTION_STRING']):
                    if len(value) > 20:
                        masked_value = f"{value[:10]}...{value[-4:]} (length: {len(value)})"
                    else:
                        masked_value = '*' * min(len(value), 8) if value else 'None'
                    display_value = masked_value
                else:
                    display_value = value
                
                message = f"{key}={display_value}"
                self.stdout.write(message)
                logger.info(f"ENV: {message}")
            
            self.stdout.write(self.style.SUCCESS('=== END ENVIRONMENT VARIABLES ==='))
        else:
            self.stdout.write(self.style.WARNING('Full environment variable logging is only available in DEBUG mode'))
            self.stdout.write('Use --azure-only to see Azure configuration in production mode.')
