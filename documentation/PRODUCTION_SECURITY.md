# Production Security Enhancements for BabelScrib

## Important Security Note

**⚠️ BabelScrib now operates without authentication - all files are accessible to all users. This significantly changes the security model.**

## Quick Security Hardening Checklist

### 1. Django Security Settings (api/settings.py)
```python
# Add these for production security
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
X_FRAME_OPTIONS = 'DENY'
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# CSRF protection (still relevant for forms)
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True

# Additional security
ALLOWED_HOSTS = ['your-domain.com']  # Set your actual domain
DEBUG = False  # Never True in production

# Note: Session security removed since authentication was removed
```

### 2. Rate Limiting (Critical without authentication)
```python
# Install: pip install django-ratelimit
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='10/m', method='POST')
@csrf_exempt
def upload_file(request):
    # Your existing upload logic
    pass

@ratelimit(key='ip', rate='50/m', method='GET')
def download_file(request, filename):
    # Your existing download logic
    pass

@ratelimit(key='ip', rate='5/m', method='POST')
def translate_documents(request):
    # Your existing translation logic
    pass
```

### 3. Enhanced Logging for Anonymous Access
```python
# In upload/views.py - add security logging for anonymous access
import logging
security_logger = logging.getLogger('security')

def download_file(request, filename):
    client_ip = request.META.get('HTTP_X_FORWARDED_FOR', 
                                request.META.get('REMOTE_ADDR', 'unknown'))
    security_logger.info(f"Anonymous file access: {client_ip} -> {filename}")
    
    # Log suspicious patterns
    if request.path.count('..') > 0:
        security_logger.warning(f"Path traversal attempt: {client_ip} -> {request.path}")
        raise Http404("File not found")
```

### 4. File Type Validation
```python
# Enhanced file validation in upload_file
ALLOWED_EXTENSIONS = {'.pdf', '.doc', '.docx', '.txt', '.pptx', '.md'}
ALLOWED_MIME_TYPES = {
    'application/pdf',
    'application/msword',
    'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    'text/plain',
    'application/vnd.ms-powerpoint',
    'application/vnd.openxmlformats-officedocument.presentationml.presentation'
}

def validate_file_security(file):
    # Check file extension
    file_ext = os.path.splitext(file.name)[1].lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"File type {file_ext} not allowed")
    
    # Check MIME type
    import magic
    mime_type = magic.from_buffer(file.read(1024), mime=True)
    file.seek(0)  # Reset file pointer
    
    if mime_type not in ALLOWED_MIME_TYPES:
        raise ValueError(f"MIME type {mime_type} not allowed")
    
    # Check file size (e.g., 50MB limit)
    if file.size > 50 * 1024 * 1024:
        raise ValueError("File too large")
```

### 5. Environment Security
```bash
# .env file - ensure these are set securely
SECRET_KEY=your-very-long-random-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Azure security
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;...
# Use Azure Key Vault for production secrets
```

### 6. Content Security Policy
```python
# Add CSP headers to prevent XSS and injection attacks
CSP_DEFAULT_SRC = "'self'"
CSP_SCRIPT_SRC = "'self' 'unsafe-inline'"
CSP_STYLE_SRC = "'self' 'unsafe-inline'"
CSP_IMG_SRC = "'self' data: https:"
CSP_CONNECT_SRC = "'self'"
```

## Anonymous Access Security Considerations

Since BabelScrib now operates without authentication:

### ⚠️ Security Implications
- **Public Access**: All uploaded files are accessible to anyone
- **No Privacy**: There's no user isolation or file ownership
- **Shared Storage**: All users share the same file space
- **Potential Abuse**: Higher risk of spam, malicious files, or resource abuse

### 🛡️ Additional Protections Recommended

1. **File Content Scanning**
   ```python
   # Consider integrating virus scanning
   # pip install pyclamd
   ```

2. **Storage Monitoring**
   ```python
   # Monitor storage usage and implement cleanup policies
   def cleanup_old_files():
       # Delete files older than X days
       pass
   ```

3. **Network Security**
   - Use CloudFlare or similar for DDoS protection
   - Implement IP-based rate limiting
   - Consider geographic restrictions if needed

## System Status: ⚠️ Public Access Mode

The current implementation provides a **public file sharing service** rather than a secured document management system. Consider whether this security model meets your requirements.

## Quick Production Deployment Checklist

1. Set `DEBUG = False` in settings
2. Configure proper `ALLOWED_HOSTS`
3. Implement rate limiting
4. Set up monitoring and alerting
5. Consider file storage lifecycle policies
6. Review and accept the public access security model
2. Configure `ALLOWED_HOSTS` with your domain
3. Enable HTTPS and set secure cookie flags
4. Set strong `SECRET_KEY`
5. Use Azure Key Vault for secrets management
6. Monitor logs for security events

Your user isolation system is solid and ready for production use!
