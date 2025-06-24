from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from django.conf import settings
from allauth.socialaccount.models import SocialApp
import os


class Command(BaseCommand):
    help = 'Verify Microsoft OAuth configuration for production'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('=== Microsoft OAuth Configuration Check ===\n'))
        
        # Check environment variables
        self.stdout.write('Environment Variables:')
        client_id = os.getenv('MICROSOFT_CLIENT_ID', '')
        client_secret = os.getenv('MICROSOFT_CLIENT_SECRET', '')
        
        self.stdout.write(f'  MICROSOFT_CLIENT_ID: {"✓ Set" if client_id else "✗ Missing"}')
        self.stdout.write(f'  MICROSOFT_CLIENT_SECRET: {"✓ Set" if client_secret else "✗ Missing"}')
        
        if client_id:
            self.stdout.write(f'  Client ID: {client_id[:8]}...{client_id[-4:]}')
        
        # Check Django settings
        self.stdout.write(f'\nDjango Settings:')
        self.stdout.write(f'  DEBUG: {settings.DEBUG}')
        self.stdout.write(f'  SITE_ID: {settings.SITE_ID}')
        self.stdout.write(f'  ACCOUNT_DEFAULT_HTTP_PROTOCOL: {getattr(settings, "ACCOUNT_DEFAULT_HTTP_PROTOCOL", "not set")}')
        self.stdout.write(f'  SECURE_PROXY_SSL_HEADER: {getattr(settings, "SECURE_PROXY_SSL_HEADER", "not set")}')
        
        # Check Site configuration
        try:
            site = Site.objects.get(id=settings.SITE_ID)
            self.stdout.write(f'\nSite Configuration:')
            self.stdout.write(f'  Site Domain: {site.domain}')
            self.stdout.write(f'  Site Name: {site.name}')
            
            # Construct expected redirect URI
            protocol = 'https' if not settings.DEBUG else 'http'
            redirect_uri = f'{protocol}://{site.domain}/accounts/microsoft/login/callback/'
            self.stdout.write(f'  Expected Redirect URI: {redirect_uri}')
            
        except Site.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'\nSite with ID {settings.SITE_ID} does not exist!'))
            self.stdout.write('Run: python manage.py fix_site_domain')
        
        # Check SocialApp configuration
        try:
            social_app = SocialApp.objects.get(provider='microsoft')
            self.stdout.write(f'\nSocialApp Configuration:')
            self.stdout.write(f'  Provider: {social_app.provider}')
            self.stdout.write(f'  Name: {social_app.name}')
            self.stdout.write(f'  Client ID: {social_app.client_id[:8]}...{social_app.client_id[-4:] if len(social_app.client_id) > 12 else social_app.client_id}')
            self.stdout.write(f'  Has Secret: {"✓" if social_app.secret else "✗"}')
            
            # Check sites association
            sites = social_app.sites.all()
            self.stdout.write(f'  Associated Sites: {[site.domain for site in sites]}')
            
            if not sites:
                self.stdout.write(self.style.WARNING('  Warning: SocialApp is not associated with any sites!'))
                
        except SocialApp.DoesNotExist:
            self.stdout.write(self.style.ERROR('\nSocialApp for Microsoft provider does not exist!'))
            self.stdout.write('Run: python manage.py setup_social_app.py')
        
        # Check HTTPS configuration
        self.stdout.write(f'\nHTTPS Configuration:')
        https_env = os.getenv('HTTPS', '')
        self.stdout.write(f'  HTTPS environment variable: {https_env or "not set"}')
        
        if not settings.DEBUG:
            self.stdout.write(f'  USE_X_FORWARDED_HOST: {getattr(settings, "USE_X_FORWARDED_HOST", "not set")}')
            self.stdout.write(f'  USE_X_FORWARDED_PORT: {getattr(settings, "USE_X_FORWARDED_PORT", "not set")}')
            self.stdout.write(f'  SESSION_COOKIE_SECURE: {getattr(settings, "SESSION_COOKIE_SECURE", "not set")}')
            self.stdout.write(f'  CSRF_COOKIE_SECURE: {getattr(settings, "CSRF_COOKIE_SECURE", "not set")}')
        
        # Final recommendations
        self.stdout.write(f'\n{self.style.SUCCESS("=== Recommendations ===")}')
        
        if not client_id or not client_secret:
            self.stdout.write(self.style.ERROR('1. Set MICROSOFT_CLIENT_ID and MICROSOFT_CLIENT_SECRET environment variables'))
        
        try:
            site = Site.objects.get(id=settings.SITE_ID)
            if site.domain in ['example.com', 'localhost', '127.0.0.1']:
                self.stdout.write(self.style.ERROR(f'2. Update site domain from {site.domain} to your production domain'))
        except Site.DoesNotExist:
            self.stdout.write(self.style.ERROR('2. Create/fix site configuration with: python manage.py fix_site_domain'))
        
        try:
            social_app = SocialApp.objects.get(provider='microsoft')
            if not social_app.sites.exists():
                self.stdout.write(self.style.ERROR('3. Associate SocialApp with site'))
        except SocialApp.DoesNotExist:
            self.stdout.write(self.style.ERROR('3. Create Microsoft SocialApp with: python manage.py setup_social_app'))
        
        if settings.DEBUG:
            self.stdout.write(self.style.WARNING('4. Ensure DEBUG=False in production'))
        
        self.stdout.write(f'\n{self.style.SUCCESS("Configuration check complete!")}')
