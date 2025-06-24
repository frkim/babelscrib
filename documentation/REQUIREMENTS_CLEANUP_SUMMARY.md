# Requirements.txt Cleanup Summary

## Overview
This document summarizes the cleanup of `requirements.txt` to remove unnecessary dependencies and streamline the project.

## Removed Dependencies

### Core Framework
- **`djangorestframework>=3.14`** - Not used; no REST API endpoints or serializers in active use
  - Related file removed: `upload/serializers.py` (contained unused DocumentSerializer)

### Authentication & Security
- **`django-azure-auth>=2.0.0`** - Not imported or used anywhere in the codebase
- **`django-azure-auth==2.0.1`** - Duplicate entry, not used
- **`django-cors-headers>=4.3.0`** - Not configured in middleware or settings

### Database
- **`psycopg2-binary>=2.9.7`** - Not needed; project uses SQLite database

### Server & Environment
- **`gunicorn>=21.2.0`** - Not used in development; production deployment uses Azure Container Apps
- **`python-dotenv>=1.0.0`** - Not imported; using django-environ instead

### Azure
- **`azure-identity>=1.15.0`** - Not imported or used; using connection strings instead of managed identity

## Retained Dependencies

### Core Django
- **`Django>=4.2,<5.0`** - Core framework
- **`django-environ>=0.11.0`** - Used in settings.py for environment variable management

### Azure Services
- **`azure-storage-blob>=12.19.0`** - Used in views.py and translation_service.py for blob storage
- **`azure-ai-translation-document==1.0.0`** - Used in translation_service.py for document translation

### Static Files
- **`whitenoise>=6.6.0`** - Used in middleware for serving static files in production

## Additional Cleanup

### Removed Files
- `upload/serializers.py` - Unused Django REST Framework serializer
- `upload/admin.py` - Unused admin configuration (Django admin not installed)

## Impact
- Reduced dependencies from 12 to 5 packages (58% reduction)
- Eliminated unused code and potential security surface
- Simplified deployment and maintenance
- Faster installation times
- Cleaner dependency tree

## Dependencies Summary (Final)
```
Django>=4.2,<5.0                      # Core framework
azure-storage-blob>=12.19.0           # Blob storage operations
azure-ai-translation-document==1.0.0  # Document translation
django-environ>=0.11.0                # Environment configuration
whitenoise>=6.6.0                     # Static file serving
```

## Verification
- All imports verified against actual code usage
- No missing dependencies identified
- All existing functionality preserved
- Django server starts successfully with cleaned requirements

## Notes
- The project now has a minimal, focused set of dependencies
- All retained dependencies are actively used in the codebase
- Future additions should be carefully evaluated for necessity
