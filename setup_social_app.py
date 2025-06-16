#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')

# Setup Django
django.setup()

from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
import environ

# Load environment variables
env = environ.Env()

# Get or create the default site
site, created = Site.objects.get_or_create(
    pk=1,
    defaults={
        'domain': 'localhost:8000',
        'name': 'BabelScrib Development'
    }
)

# Create Microsoft Social Application
microsoft_app, created = SocialApp.objects.get_or_create(
    provider='microsoft',
    defaults={
        'name': 'Microsoft',
        'client_id': env('MICROSOFT_CLIENT_ID', default='fcfbaf73-654e-49a7-9141-b994192888c6'),
        'secret': env('MICROSOFT_CLIENT_SECRET', default=''),
    }
)

# Associate with the site
microsoft_app.sites.add(site)

if created:
    print(f"✓ Created Microsoft SocialApp: {microsoft_app.name}")
else:
    print(f"✓ Microsoft SocialApp already exists: {microsoft_app.name}")
    # Update the app in case credentials changed
    microsoft_app.client_id = env('MICROSOFT_CLIENT_ID', default='fcfbaf73-654e-49a7-9141-b994192888c6')
    microsoft_app.secret = env('MICROSOFT_CLIENT_SECRET', default='')
    microsoft_app.save()
    print("✓ Updated Microsoft SocialApp credentials")

print(f"✓ Associated with site: {site.domain}")
print(f"Client ID: {microsoft_app.client_id}")
print(f"Secret: {'*' * len(microsoft_app.secret) if microsoft_app.secret else 'NOT SET'}")

print("\nSocialApp setup complete!")
print("You can now test the Microsoft login at: http://localhost:8000/accounts/microsoft/login/")
