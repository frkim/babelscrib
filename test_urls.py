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

from django.urls import reverse, NoReverseMatch

try:
    # Test different URL patterns that might work
    url_patterns_to_test = [
        ('socialaccount_login', {'provider': 'microsoft'}),
        ('socialaccount_login', None),
        ('microsoft_login', None),
        ('account_login', None),
    ]
    
    for pattern_name, kwargs in url_patterns_to_test:
        try:
            if kwargs:
                url = reverse(pattern_name, kwargs=kwargs)
            else:
                url = reverse(pattern_name)
            print(f"✓ {pattern_name}: {url}")
        except NoReverseMatch as e:
            print(f"✗ {pattern_name}: {e}")

except Exception as e:
    print(f"Error: {e}")

# Also list all URL patterns that contain 'social' or 'microsoft'
from django.urls import get_resolver
resolver = get_resolver()

def print_urls(urlpatterns, prefix=''):
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            print_urls(pattern.url_patterns, prefix + str(pattern.pattern))
        else:
            name = getattr(pattern, 'name', None)
            if name and ('social' in name.lower() or 'microsoft' in name.lower()):
                print(f"Found URL: {prefix}{pattern.pattern} -> {name}")

print("\nAll social/microsoft related URLs:")
print_urls(resolver.url_patterns)
