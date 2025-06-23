"""
Django management command to add a specific site for production deployment.

This command creates a Site object with the exact domain and name specified,
regardless of the current DEBUG setting.

Usage:
    python manage.py add_production_site
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.sites.models import Site
from django.conf import settings


class Command(BaseCommand):
    help = 'Adds a specific site for production deployment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--domain',
            type=str,
            help='Domain name for the site',
            default='www.babelscrib.com'
        )
        parser.add_argument(
            '--name',
            type=str,
            help='Display name for the site',
            default='www.babelscrib.com'
        )
        parser.add_argument(
            '--site-id',
            type=int,
            help='Site ID to use (if updating existing site)',
            default=None
        )

    def handle(self, *args, **options):
        domain = options['domain']
        site_name = options['name']
        site_id = options['site_id']
        
        self.stdout.write(self.style.SUCCESS('=== Adding Production Site ==='))
        self.stdout.write(f'Domain: {domain}')
        self.stdout.write(f'Display Name: {site_name}')
        
        # Remove development site if it exists (for production cleanup)
        try:
            dev_site = Site.objects.filter(
                name="www.babelscrib.com Development", 
                domain="localhost:8000"
            ).first()
            if dev_site:
                dev_site_id = dev_site.pk
                dev_site.delete()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Removed development site ID {dev_site_id}: www.babelscrib.com Development (localhost:8000)'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING('Development site not found: www.babelscrib.com Development (localhost:8000)')
                )
        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'Warning: Could not remove development site: {str(e)}')
            )
        
        try:
            if site_id:
                # Update existing site by ID
                try:
                    site = Site.objects.get(pk=site_id)
                    old_domain = site.domain
                    old_name = site.name
                    site.domain = domain
                    site.name = site_name
                    site.save()
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Updated Site ID {site_id}: {old_name} ({old_domain}) → {site.name} ({site.domain})'
                        )
                    )
                except Site.DoesNotExist:
                    raise CommandError(f'Site with ID {site_id} does not exist!')
            else:
                # Check if site with this domain already exists
                existing_site = None
                try:
                    existing_site = Site.objects.get(domain=domain)
                    self.stdout.write(
                        self.style.WARNING(
                            f'Site with domain {domain} already exists (ID: {existing_site.pk}, Name: {existing_site.name})'
                        )
                    )
                    
                    # Update the name if it's different
                    if existing_site.name != site_name:
                        old_name = existing_site.name
                        existing_site.name = site_name
                        existing_site.save()
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'✓ Updated site name: {old_name} → {site_name}'
                            )
                        )
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Site already correctly configured')
                        )
                    
                    site = existing_site
                    
                except Site.DoesNotExist:
                    # Create new site
                    site = Site.objects.create(
                        domain=domain,
                        name=site_name
                    )
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Created new Site ID {site.pk}: {site.name} ({site.domain})'
                        )
                    )
            
            # Display summary
            self.stdout.write('\n' + '='*50)
            self.stdout.write(self.style.SUCCESS('✓ Site configuration completed!'))
            self.stdout.write(f'Site ID: {site.pk}')
            self.stdout.write(f'Domain: {site.domain}')
            self.stdout.write(f'Display Name: {site.name}')
            
            # Show all existing sites
            self.stdout.write('\nAll existing sites:')
            for s in Site.objects.all().order_by('pk'):
                marker = ' ← NEW' if s.pk == site.pk else ''
                self.stdout.write(f'  ID {s.pk}: {s.name} ({s.domain}){marker}')
            
            # Check if this matches SITE_ID setting
            current_site_id = getattr(settings, 'SITE_ID', 1)
            if site.pk == current_site_id:
                self.stdout.write(
                    self.style.SUCCESS(f'\n✓ This site matches the current SITE_ID setting ({current_site_id})')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'\n⚠ Note: Current SITE_ID setting is {current_site_id}, but this site has ID {site.pk}'
                    )
                )
                self.stdout.write(
                    f'  If you want to use this site, update SITE_ID in settings.py to {site.pk}'
                )
            
        except Exception as e:
            raise CommandError(f'Error adding site: {str(e)}')
