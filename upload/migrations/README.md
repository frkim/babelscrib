# Django Migrations - Upload App

## Overview
This directory contains Django database migrations for the `upload` app, which manages document upload and translation functionality for BabelScrib.

## Migration History

### 0001_initial.py
**Created:** June 9, 2025  
**Description:** Initial migration creating the core database schema

**Models Created:**
- **Document Model**: Core document tracking with Azure blob integration
  - `title`: Document title (CharField, max_length=255)
  - `file`: File upload field (FileField, upload_to='documents/')
  - `uploaded_at`: Timestamp of upload (DateTimeField, auto_now_add=True)
  - `user_email`: Email of uploader (EmailField)
  - `user_id_hash`: Hashed user identifier (CharField, max_length=64, indexed)
  - `blob_name`: Azure blob storage filename (CharField, max_length=500)
  - `user_blob_name`: User-specific blob name (CharField, max_length=500)
  - `is_translated`: Translation status flag (BooleanField, default=False)
  - `translation_language`: Target language code (CharField, max_length=10, nullable)

- **UserSession Model**: Session management for user isolation
  - `session_key`: Unique session identifier (CharField, max_length=40, unique)
  - `user_email`: Associated user email (EmailField)
  - `user_id_hash`: Hashed user identifier (CharField, max_length=64)
  - `created_at`: Session creation time (DateTimeField, auto_now_add=True)
  - `last_activity`: Last activity timestamp (DateTimeField, auto_now=True)

**Indexes Created:**
- `upload_docu_user_em_ae5f68_idx`: Composite index on (user_email, uploaded_at)
- `upload_docu_user_id_ed1b55_idx`: Index on user_id_hash
- `upload_user_session_f7273a_idx`: Index on session_key
- `upload_user_user_em_f1118d_idx`: Index on user_email

### 0002_delete_usersession_and_more.py
**Created:** June 24, 2025  
**Description:** Architecture simplification - removed user session management and user-specific fields

**Changes Made:**
1. **Deleted UserSession Model** - Removed complex session management
2. **Simplified Document Model:**
   - Removed `user_email` field
   - Removed `user_id_hash` field  
   - Removed `user_blob_name` field
   - Removed user-specific indexes
   - Added simple `uploaded_at` index for chronological queries

**Rationale:**
- Simplified architecture for better maintainability
- Removed user isolation complexity (not required for current use case)
- Focus on core document translation functionality
- Improved performance with simpler indexing strategy

## Current Schema

### Document Model (Final State)
```python
class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    blob_name = models.CharField(max_length=500)  # Azure storage reference
    is_translated = models.BooleanField(default=False)
    translation_language = models.CharField(max_length=10, blank=True, null=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['uploaded_at']),  # Chronological queries
        ]
```

## Database Indexes

### Current Indexes
- **`upload_docu_uploade_0f101f_idx`**: Index on `uploaded_at` field
  - **Purpose**: Optimize chronological document queries
  - **Usage**: Document listing, cleanup operations, time-based filtering

### Index Strategy
- **Simple and focused**: Single-field indexes for common queries
- **Performance optimized**: Indexes align with actual query patterns
- **Maintenance friendly**: Fewer indexes = easier maintenance

## Migration Commands

### Check Migration Status
```bash
python manage.py showmigrations upload
```

### Apply Migrations
```bash
python manage.py migrate upload
```

### Create New Migrations
```bash
python manage.py makemigrations upload
```

### Rollback Migrations
```bash
# Rollback to previous migration
python manage.py migrate upload 0001

# Rollback all app migrations
python manage.py migrate upload zero
```

## Best Practices

### Before Making Changes
1. **Always backup database** before applying migrations in production
2. **Test migrations** in development environment first
3. **Review migration files** before applying to ensure correctness
4. **Check for data loss** using `--dry-run` flag

### Migration Guidelines
1. **Atomic changes**: Keep migrations focused on single logical changes
2. **Reversible operations**: Ensure migrations can be safely rolled back
3. **Data preservation**: Use data migrations when restructuring existing data
4. **Index optimization**: Add/remove indexes based on actual query patterns

### Performance Considerations
- **Large tables**: Consider using `RunSQL` for complex schema changes
- **Production deployments**: Use database migration tools for zero-downtime deployments
- **Index creation**: Be aware that adding indexes to large tables can be slow

## Troubleshooting

### Common Issues
1. **Migration conflicts**: Resolve by merging or recreating conflicting migrations
2. **Rollback failures**: Some operations (like dropping columns) cannot be reversed
3. **Performance issues**: Large table migrations may require maintenance windows

### Emergency Procedures
1. **Failed migration**: Use `python manage.py migrate --fake` (with caution)
2. **Corrupt migration state**: Reset migration history and recreate from scratch
3. **Production issues**: Have rollback plan ready before applying migrations

## Azure Integration Notes

### Blob Storage Fields
- **`blob_name`**: Stores the Azure Blob Storage filename/path
- **Purpose**: Links database records to files stored in Azure Storage
- **Format**: Typically UUID-based filenames for uniqueness

### Translation Integration
- **`is_translated`**: Boolean flag indicating translation completion
- **`translation_language`**: ISO language code for target translation language
- **Usage**: Tracks translation workflow state

## Future Considerations

### Potential Enhancements
1. **Audit trail**: Add created_by/modified_by fields for tracking
2. **Soft delete**: Add deleted_at field instead of hard deletes
3. **File metadata**: Add file size, MIME type, checksum fields
4. **Translation history**: Track multiple translations per document
5. **User management**: Re-introduce user fields if authentication is added

### Scalability Notes
- Current schema supports horizontal scaling
- Consider partitioning by upload date for very large datasets
- Monitor index performance as data volume grows

---
*Last updated: June 24, 2025*
