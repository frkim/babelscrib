"""
Django management command to set up Site and SocialApp for production deployment.

This command creates the required Site object and Microsoft SocialApp that are
needed for django-allauth to work properly in production.

Usage:
    python manage.py setup_production_site
    python manage.py setup_production_site --domain www.babelscrib.com --name "BabelScrib Production"
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings
import environ
import os


class Command(BaseCommand):
    help = 'Sets up Site and Microsoft SocialApp for production deployment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            help='Domain name for the site (default: www.babelscrib.com)',
            default='www.babelscrib.com'
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Display name for the site (default: BabelScrib)',
            default='BabelScrib'
        )
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Force update existing site and social app',
            default=False
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('=== Setting up production site configuration ==='))
        
        # Load environment variables
        env = environ.Env()
        
        # Determine if we're in production based on DEBUG setting
        is_production = not getattr(settings, 'DEBUG', True)
        
        # Get site configuration
        domain = options['domain']
        site_name = options['name']
        force_update = options['force_update']
        
        # Adjust domain based on environment if not explicitly provided
        if domain == 'www.babelscrib.com' and not is_production:
            domain = 'localhost:8000'
            site_name = f'{site_name} Development'
        
        self.stdout.write(f'Environment: {"Production" if is_production else "Development"}')
        self.stdout.write(f'Domain: {domain}')
        self.stdout.write(f'Site Name: {site_name}')
        
        try:
            # Step 1: Create or update Site
            self.stdout.write('\n1. Setting up Site object...')
            
            site, created = Site.objects.get_or_create(
                pk=getattr(settings, 'SITE_ID', 1),
                defaults={
                    'domain': domain,
                    'name': site_name
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created new Site: {site.name} ({site.domain})')
                )
            else:
                if force_update or site.domain != domain or site.name != site_name:
                    old_domain = site.domain
                    old_name = site.name
                    site.domain = domain
                    site.name = site_name
                    site.save()
                    self.stdout.write(
                        self.style.WARNING(
                            f'✓ Updated Site: {old_name} ({old_domain}) → {site.name} ({site.domain})'
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Site already exists: {site.name} ({site.domain})')
                    )
            
            # Step 2: Create or update Microsoft SocialApp
            self.stdout.write('\n2. Setting up Microsoft SocialApp...')
            
            # Get Microsoft credentials from environment
            client_id = env('MICROSOFT_CLIENT_ID', default='')
            client_secret = env('MICROSOFT_CLIENT_SECRET', default='')
            
            if not client_id:
                self.stdout.write(
                    self.style.WARNING(
                        '⚠ MICROSOFT_CLIENT_ID not found in environment variables'
                    )
                )
                client_id = 'your-client-id-here'
            
            if not client_secret:
                self.stdout.write(
                    self.style.WARNING(
                        '⚠ MICROSOFT_CLIENT_SECRET not found in environment variables'
                    )
                )
            
            # Create or get Microsoft SocialApp
            microsoft_app, created = SocialApp.objects.get_or_create(
                provider='microsoft',
                defaults={
                    'name': 'Microsoft',
                    'client_id': client_id,
                    'secret': client_secret,
                }
            )
            
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created Microsoft SocialApp: {microsoft_app.name}')
                )
            else:
                # Update credentials if they've changed or if forced
                updated = False
                if force_update or microsoft_app.client_id != client_id:
                    microsoft_app.client_id = client_id
                    updated = True
                if force_update or microsoft_app.secret != client_secret:
                    microsoft_app.secret = client_secret
                    updated = True
                
                if updated:
                    microsoft_app.save()
                    self.stdout.write(
                        self.style.WARNING('✓ Updated Microsoft SocialApp credentials')
                    )
                else:
                    self.stdout.write(
                        self.style.SUCCESS(f'✓ Microsoft SocialApp already exists: {microsoft_app.name}')
                    )
            
            # Step 3: Associate SocialApp with Site
            self.stdout.write('\n3. Associating SocialApp with Site...')
            
            if site in microsoft_app.sites.all():
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Microsoft SocialApp already associated with site: {site.domain}')
                )
            else:
                microsoft_app.sites.add(site)
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Associated Microsoft SocialApp with site: {site.domain}')
                )
            
            # Step 4: Verify configuration
            self.stdout.write('\n4. Verifying configuration...')
            
            # Check that Site exists and has correct ID
            try:
                site_check = Site.objects.get(pk=getattr(settings, 'SITE_ID', 1))
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Site ID {site_check.pk} exists: {site_check.domain}')
                )
            except Site.DoesNotExist:
                raise CommandError(f'Site with ID {getattr(settings, "SITE_ID", 1)} does not exist!')
            
            # Check SocialApp
            try:
                app_check = SocialApp.objects.get(provider='microsoft')
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Microsoft SocialApp exists with client_id: {app_check.client_id[:8]}...')
                )
                
                # Check association
                if site_check in app_check.sites.all():
                    self.stdout.write(
                        self.style.SUCCESS('✓ SocialApp is properly associated with the site')
                    )
                else:
                    raise CommandError('SocialApp is not associated with the site!')
                    
            except SocialApp.DoesNotExist:
                raise CommandError('Microsoft SocialApp does not exist!')
            
            # Step 5: Summary
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('✓ Site and SocialApp setup completed successfully!'))
            self.stdout.write(f'Site: {site_check.name} ({site_check.domain})')
            self.stdout.write(f'Client ID: {app_check.client_id}')
            self.stdout.write(f'Secret: {"*" * len(app_check.secret) if app_check.secret else "NOT SET"}')
            
            if is_production:
                self.stdout.write(f'\nYou can now test Microsoft login at: https://{site_check.domain}/accounts/microsoft/login/')
            else:
                self.stdout.write(f'\nYou can now test Microsoft login at: http://{site_check.domain}/accounts/microsoft/login/')
            
            if not client_secret:
                self.stdout.write(
                    self.style.WARNING(
                        '\n⚠ WARNING: MICROSOFT_CLIENT_SECRET is not set. '
                        'Microsoft authentication will not work until this is configured.'
                    )
                )
            
        except Exception as e:
            raise CommandError(f'Error setting up site configuration: {str(e)}')
