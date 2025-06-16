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

# Try different URL patterns
url_patterns_to_try = [
    'microsoft_login',
    'socialaccount_login',
    'socialaccount_provider_login',
    ('socialaccount_login', {'provider': 'microsoft'}),
]

print("Testing URL patterns:")
for pattern in url_patterns_to_try:
    try:
        if isinstance(pattern, tuple):
            url = reverse(pattern[0], kwargs=pattern[1])
            print(f"✓ {pattern[0]} with {pattern[1]}: {url}")
        else:
            url = reverse(pattern)
            print(f"✓ {pattern}: {url}")
    except NoReverseMatch as e:
        print(f"✗ {pattern}: Failed")

# Check what URLs exist that contain social or microsoft
from django.conf import settings
from django.urls import get_resolver

print("\nSearching for social/microsoft related URLs...")
resolver = get_resolver()

def find_social_urls(urlpatterns, prefix=''):
    urls = []
    for pattern in urlpatterns:
        if hasattr(pattern, 'name') and pattern.name:
            if 'social' in pattern.name.lower() or 'microsoft' in pattern.name.lower():
                urls.append(pattern.name)
        if hasattr(pattern, 'url_patterns'):
            urls.extend(find_social_urls(pattern.url_patterns, prefix))
    return urls

social_urls = find_social_urls(resolver.url_patterns)
print("Found URLs:", social_urls)
