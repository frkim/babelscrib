"""
Test Django i18n setup
"""
from django.core.management.base import BaseCommand
from django.utils import translation
from django.utils.translation import gettext as _

class Command(BaseCommand):
    help = 'Test Django i18n setup'

    def handle(self, *args, **options):
        # Test with English
        translation.activate('en')
        self.stdout.write(f"English: {_('Document Upload')}")
        
        # Test with French  
        translation.activate('fr')
        self.stdout.write(f"French: {_('Document Upload')}")
        
        # Reset to default
        translation.deactivate()
        self.stdout.write("i18n test completed!")
