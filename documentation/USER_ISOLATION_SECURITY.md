# User Isolation and Security Implementation

## Overview

This document describes the user isolation implementation for the BabelScrib document translation application. The solution provides secure file access control ensuring users can only access their own documents.

## Security Features Implemented

### 1. Session-Based User Identification
- **User Sessions**: Each user is identified by their email address and a Django session
- **Session Tracking**: `UserSession` model tracks active user sessions
- **Automatic Cleanup**: Old sessions (>24 hours) are automatically cleaned up

### 2. File Isolation
- **User-Specific Blob Names**: Files are stored with user-specific prefixes in Azure Blob Storage
- **Hash-Based Identification**: User emails are hashed for privacy and used as folder prefixes
- **Database Tracking**: `Document` model tracks file ownership and metadata

### 3. Access Control
- **Download Protection**: Users can only download files they uploaded
- **Session Validation**: All sensitive operations require valid user sessions
- **File Ownership Verification**: Download requests validate file ownership before serving

## Implementation Details

### Database Models

#### Document Model
```python
class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user_email = models.EmailField()
    user_id_hash = models.CharField(max_length=64, db_index=True)
    blob_name = models.CharField(max_length=500)  # Original filename
    user_blob_name = models.CharField(max_length=500)  # User-specific blob name
    is_translated = models.BooleanField(default=False)
    translation_language = models.CharField(max_length=10, blank=True, null=True)
```

#### UserSession Model
```python
class UserSession(models.Model):
    session_key = models.CharField(max_length=40, unique=True)
    user_email = models.EmailField()
    user_id_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
```

### File Naming Convention

Files are stored in Azure Blob Storage with the following structure:
```
Container: source/
├── {user_hash}/document1.pdf
├── {user_hash}/document2.docx
└── {another_user_hash}/document3.pdf

Container: target/
├── {user_hash}/translated_document1.pdf
├── {user_hash}/translated_document2.docx
└── {another_user_hash}/translated_document3.pdf
```

Where `{user_hash}` is a 16-character SHA256 hash of the user's email address.

### Security Flow

#### File Upload
1. User provides email address
2. System creates/updates user session
3. File is uploaded with user-specific blob name: `{user_hash}/{filename}`
4. Document record is created in database with ownership information

#### File Translation
1. System validates user session (required)
2. Creates user-specific source and target URIs
3. Translation service processes only files in user's folder
4. Translated files are stored in user's target folder

#### File Download
1. System validates user session (required)
2. Verifies file ownership through database lookup
3. Constructs user-specific blob path
4. Downloads and serves file only if user owns it
5. Optionally cleans up file after download

## Security Benefits

### 1. Data Isolation
- **Physical Separation**: Files are stored in separate blob paths per user
- **Logical Separation**: Database enforces ownership relationships
- **No Cross-User Access**: Users cannot access files from other users

### 2. Privacy Protection
- **Email Hashing**: User emails are hashed before being used as identifiers
- **Session-Based Auth**: No passwords or sensitive data stored
- **Automatic Cleanup**: Sessions and files are cleaned up automatically

### 3. Attack Prevention
- **Path Traversal Protection**: File names are sanitized
- **Session Hijacking Protection**: Sessions timeout automatically
- **Unauthorized Access Protection**: All operations validate ownership

## Configuration

### Environment Variables
```bash
# Required for Azure Blob Storage
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_CONTAINER_NAME_SOURCE=source
AZURE_STORAGE_CONTAINER_NAME_TARGET=target

# Required for Translation Service
AZURE_TRANSLATOR_KEY=your_translator_key
AZURE_TRANSLATOR_ENDPOINT=your_translator_endpoint
```

### Django Settings
```python
# Ensure session middleware is enabled
MIDDLEWARE = [
    'django.contrib.sessions.middleware.SessionMiddleware',
    # ... other middleware
]

# Session configuration
SESSION_COOKIE_AGE = 86400  # 24 hours
SESSION_EXPIRE_AT_BROWSER_CLOSE = True
```

## API Endpoints

### Protected Endpoints (Require User Session)
- `POST /translate/` - Start document translation
- `GET /download/<filename>/` - Download translated file
- `GET /api/files/` - List user's files

### Public Endpoints
- `POST /upload/` - Upload files (creates session)
- `GET /` - Main upload page

## Usage Flow

1. **User uploads files**:
   - Provides email address
   - Files are stored with user-specific names
   - Session is created/updated

2. **User starts translation**:
   - Session is validated
   - Translation processes only user's files
   - Results are stored in user's target folder

3. **User downloads results**:
   - Session is validated
   - File ownership is verified
   - File is served and optionally cleaned up

## Migration and Deployment

### Database Migrations
```bash
python manage.py makemigrations upload
python manage.py migrate
```

### Existing Data Migration
For existing installations with data, a migration script should be created to:
1. Associate existing files with user email addresses
2. Generate user-specific blob names
3. Move files to user-specific locations in blob storage

## Monitoring and Maintenance

### Recommended Monitoring
- Track failed authentication attempts
- Monitor blob storage usage per user
- Alert on unusual file access patterns
- Monitor session cleanup frequency

### Regular Maintenance
- Review and clean up old sessions
- Monitor blob storage costs
- Review access logs for security issues
- Update user hash algorithm if needed

## Future Enhancements

### Potential Improvements
1. **Real User Authentication**: Implement proper user accounts with passwords
2. **Admin Interface**: Django admin interface for user management
3. **File Sharing**: Allow users to share files with specific other users
4. **File Versioning**: Track multiple versions of the same document
5. **Audit Logging**: Comprehensive logging of all user actions
6. **Rate Limiting**: Prevent abuse by limiting upload/translation frequency

### Security Hardening
1. **HTTPS Enforcement**: Ensure all traffic is encrypted
2. **CSRF Protection**: Verify CSRF tokens on all forms
3. **Input Validation**: Enhanced validation for all user inputs
4. **File Type Restrictions**: Stricter file type validation
5. **Virus Scanning**: Integrate virus scanning for uploaded files

## Testing

### Test Cases
1. **Isolation Tests**: Verify users cannot access other users' files
2. **Session Tests**: Verify session creation, validation, and cleanup
3. **Upload Tests**: Verify files are stored with correct ownership
4. **Download Tests**: Verify only authorized downloads are allowed
5. **Translation Tests**: Verify translations only process user's files

### Security Testing
1. **Path Traversal**: Attempt to access files outside user's folder
2. **Session Hijacking**: Test session security
3. **Cross-User Access**: Attempt to access other users' files
4. **Input Injection**: Test for SQL injection and XSS vulnerabilities
