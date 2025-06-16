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

# Update the existing Microsoft SocialApp
try:
    microsoft_app = SocialApp.objects.get(provider='microsoft')
    
    # Update credentials
    microsoft_app.client_id = env('MICROSOFT_CLIENT_ID', default='fcfbaf73-654e-49a7-9141-b994192888c6')
    microsoft_app.secret = env('MICROSOFT_CLIENT_SECRET', default='')
    
    # Add provider-specific settings as JSON in the 'key' field
    # This is where we can store additional provider configuration
    import json
    provider_settings = {
        'tenant': env('MICROSOFT_TENANT_ID', default='common'),
        'scope': ['openid', 'profile', 'email'],
        'auth_params': {
            'access_type': 'online',
        }
    }
    microsoft_app.key = json.dumps(provider_settings)
    
    microsoft_app.save()
    
    print(f"✓ Updated Microsoft SocialApp")
    print(f"  Client ID: {microsoft_app.client_id}")
    print(f"  Secret: {'*' * len(microsoft_app.secret) if microsoft_app.secret else 'NOT SET'}")
    print(f"  Provider settings: {microsoft_app.key}")
    
    # Ensure it's associated with the correct site
    current_site = Site.objects.get(pk=1)
    microsoft_app.sites.clear()
    microsoft_app.sites.add(current_site)
    
    print(f"✓ Associated with site: {current_site.domain}")
    
except SocialApp.DoesNotExist:
    print("✗ Microsoft SocialApp not found. Run setup_social_app.py first.")
except Exception as e:
    print(f"✗ Error: {e}")

print("\nTesting configuration:")
print("- Visit: http://localhost:8000/accounts/microsoft/login/")
print("- The MultipleObjectsReturned error should be resolved.")
