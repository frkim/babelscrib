#!/usr/bin/env python
"""
Script to configure Django Sites and Microsoft SocialApp for production.
This script will:
1. Update the Site with domain 'www.babelscrib.com'
2. Configure Microsoft SocialApp with environment variables
3. Associate the SocialApp with the production site
"""

import os
import sys
import django
import json

# Add the project directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')

# Setup Django
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
import environ

# Load environment variables
env = environ.Env()

def main():
    print("=== Configuring Django Sites and Microsoft Authentication for Production ===")
    
    # Step 1: Update Site configuration for production
    print("\n1. Configuring Django Site for production...")
    
    try:
        site = Site.objects.get(pk=1)
        old_domain = site.domain
        old_name = site.name
        
        # Update site for production
        site.domain = 'www.babelscrib.com'
        site.name = 'BabelScrib'
        site.save()
        
        print(f"✓ Updated Site: {old_name} ({old_domain}) → {site.name} ({site.domain})")
        
    except Site.DoesNotExist:
        # Create new site if it doesn't exist
        site = Site.objects.create(
            pk=1,
            domain='www.babelscrib.com',
            name='BabelScrib'
        )
        print(f"✓ Created new Site: {site.name} ({site.domain})")
    
    # Step 2: Configure Microsoft SocialApp
    print("\n2. Configuring Microsoft SocialApp...")
    
    # Get Microsoft credentials from environment
    client_id = env('MICROSOFT_CLIENT_ID', default='')
    client_secret = env('MICROSOFT_CLIENT_SECRET', default='')
    
    if not client_id:
        print("⚠ WARNING: MICROSOFT_CLIENT_ID not found in environment variables")
        client_id = 'your-client-id-here'
    
    if not client_secret:
        print("⚠ WARNING: MICROSOFT_CLIENT_SECRET not found in environment variables")
    
    # Microsoft provider configuration
    key_config = {
        "tenant": "common",
        "scope": ["openid", "profile", "email"],
        "auth_params": {"access_type": "online"}
    }
    key_config_json = json.dumps(key_config)
    
    try:
        # Get existing Microsoft SocialApp
        microsoft_app = SocialApp.objects.get(provider='microsoft')
        
        # Update configuration
        microsoft_app.name = 'Microsoft'
        microsoft_app.client_id = client_id
        microsoft_app.secret = client_secret
        microsoft_app.key = key_config_json
        microsoft_app.save()
        
        print(f"✓ Updated Microsoft SocialApp")
        
    except SocialApp.DoesNotExist:
        # Create new Microsoft SocialApp
        microsoft_app = SocialApp.objects.create(
            provider='microsoft',
            name='Microsoft',
            client_id=client_id,
            secret=client_secret,
            key=key_config_json
        )
        print(f"✓ Created Microsoft SocialApp")
    
    # Step 3: Associate SocialApp with Site
    print("\n3. Associating SocialApp with Site...")
    
    # Clear existing site associations and add the production site
    microsoft_app.sites.clear()
    microsoft_app.sites.add(site)
    
    print(f"✓ Associated Microsoft SocialApp with site: {site.domain}")
    
    # Step 4: Verification
    print("\n4. Verifying configuration...")
    
    # Verify site
    site_check = Site.objects.get(pk=1)
    print(f"✓ Site ID 1: {site_check.name} ({site_check.domain})")
    
    # Verify SocialApp
    app_check = SocialApp.objects.get(provider='microsoft')
    print(f"✓ Microsoft SocialApp: Client ID {app_check.client_id[:8]}...")
    print(f"✓ Secret configured: {'Yes' if app_check.secret else 'No'}")
    
    # Verify association
    if site_check in app_check.sites.all():
        print(f"✓ SocialApp properly associated with {site_check.domain}")
    else:
        print("✗ ERROR: SocialApp not associated with site!")
        return False
    
    # Step 5: Summary
    print("\n" + "="*60)
    print("✓ Production configuration completed successfully!")
    print(f"Site: {site_check.name} ({site_check.domain})")
    print(f"Provider: Microsoft")
    print(f"Client ID: {app_check.client_id}")
    print(f"Secret: {'*' * len(app_check.secret) if app_check.secret else 'NOT SET'}")
    print(f"Configuration: {app_check.key}")
    
    print(f"\nYou can now test Microsoft login at: https://{site_check.domain}/accounts/microsoft/login/")
    
    if not client_secret:
        print("\n⚠ WARNING: MICROSOFT_CLIENT_SECRET is not set.")
        print("Microsoft authentication will not work until this is configured.")
    
    return True

if __name__ == '__main__':
    try:
        success = main()
        if success:
            print("\n✓ Setup completed successfully!")
        else:
            print("\n✗ Setup failed!")
            sys.exit(1)
    except Exception as e:
        print(f"\n✗ Error during setup: {str(e)}")
        sys.exit(1)
