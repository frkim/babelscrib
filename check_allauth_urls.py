#!/usr/bin/env python
import os
import django

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')

# Setup Django
django.setup()

# Import after Django setup
from django.urls import get_resolver
from django.urls.exceptions import NoReverseMatch
from django.urls import reverse

# Print all URL patterns that might be related to allauth
def print_all_urls(urlpatterns, prefix=''):
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            # This is an include() pattern
            new_prefix = prefix + str(pattern.pattern)
            print_all_urls(pattern.url_patterns, new_prefix)
        else:
            # This is a regular URL pattern
            name = getattr(pattern, 'name', 'No name')
            full_pattern = prefix + str(pattern.pattern)
            print(f"{full_pattern} -> {name}")

resolver = get_resolver()
print("All URL patterns:")
print_all_urls(resolver.url_patterns)

print("\n" + "="*50)
print("Testing specific URL patterns:")

# Test different patterns
patterns_to_test = [
    'account_login',
    'socialaccount_login',
    'microsoft_login', 
    'socialaccount_providers',
]

for pattern in patterns_to_test:
    try:
        url = reverse(pattern)
        print(f"✓ {pattern}: {url}")
    except NoReverseMatch as e:
        print(f"✗ {pattern}: Not found")
        
# Test with provider parameter
try:
    url = reverse('socialaccount_login', kwargs={'provider': 'microsoft'})
    print(f"✓ socialaccount_login with provider: {url}")
except NoReverseMatch as e:
    print(f"✗ socialaccount_login with provider: Not found")
