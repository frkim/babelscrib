# Azure Storage Troubleshooting and Testing Enhancement

## Overview

This enhancement adds comprehensive Azure Storage connectivity testing and detailed error reporting to help diagnose production deployment issues. The "Storage configuration invalid" error you encountered can now be thoroughly analyzed and resolved.

## New Features Added

### 1. Comprehensive Storage Test Endpoint

**URL:** `/test-azure-storage/`

**Description:** A comprehensive test that validates:
- Azure Storage connection string format and validity
- Blob Service Client initialization  
- Container existence and creation capabilities
- Blob CRUD operations (Create, Read, Update, Delete)
- Translation service configuration
- Account-level permissions and connectivity

### 2. Enhanced Error Reporting

All storage-related endpoints now provide:
- Detailed error messages with specific failure reasons
- Troubleshooting suggestions
- Reference to the test endpoint for diagnostics

### 3. User-Friendly Test Interface

The test endpoint provides both:
- **HTML Interface**: Visit `/test-azure-storage/` in a browser for a visual test report
- **JSON API**: Call the endpoint with JSON headers for programmatic testing

## Production Troubleshooting Guide

### Step 1: Access the Storage Test

1. **In Production**: Navigate to `https://your-domain.com/test-azure-storage/`
2. **Locally**: Visit `http://localhost:8000/test-azure-storage/`

### Step 2: Run the Comprehensive Test

Click "Run Storage Test" to execute all diagnostics. The test will:

1. **Connection String Validation**
   - Checks if `AZURE_STORAGE_CONNECTION_STRING` environment variable exists
   - Validates format (DefaultEndpointsProtocol, AccountName, AccountKey)
   - Handles URL encoding issues
   - Tests BlobServiceClient initialization

2. **Container Operations Testing**
   - Tests both source and target containers
   - Verifies container existence and creation permissions
   - Lists container properties and blob counts
   - Tests container access permissions

3. **Blob CRUD Operations**
   - Creates a test blob with timestamp
   - Verifies blob existence and reads content
   - Validates content integrity
   - Tests blob properties retrieval
   - Cleans up test blob
   - Verifies deletion

4. **Translation Service Configuration**
   - Validates translation service setup
   - Checks API key configuration
   - Tests service initialization

### Step 3: Analyze Results

The test provides detailed results for each operation:

- ✅ **Success**: Operation completed successfully
- ❌ **Failed**: Operation failed with specific error message
- ⚠️ **Warning**: Operation completed with warnings

### Common Issues and Solutions

#### 1. "Connection String Missing"
**Problem**: `AZURE_STORAGE_CONNECTION_STRING` environment variable not set

**Solutions**:
```bash
# Set environment variable (replace with your actual connection string)
export AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=youraccount;AccountKey=yourkey;EndpointSuffix=core.windows.net"
```

#### 2. "Connection String Invalid Format"
**Problem**: Connection string doesn't contain required components

**Check for**:
- `DefaultEndpointsProtocol=https`
- `AccountName=yourstorageaccount`
- `AccountKey=your-access-key`
- `EndpointSuffix=core.windows.net`

#### 3. "URL Encoding Issues"
**Problem**: Connection string is URL-encoded when retrieved from environment

**Solution**: The system now automatically detects and decodes URL-encoded connection strings

#### 4. "Container Access Denied"
**Problem**: Storage account doesn't allow container operations

**Solutions**:
- Verify storage account access keys are correct
- Check storage account firewall settings
- Ensure storage account allows public access or configure appropriate access policies
- Verify network connectivity to Azure Storage

#### 5. "Blob Operations Failed"
**Problem**: Can access containers but cannot create/read/delete blobs

**Solutions**:
- Check storage account tier and capabilities
- Verify blob storage permissions
- Check for storage account restrictions

## Environment Variables Required

Ensure these environment variables are properly set in production:

```bash
# Required for storage operations
AZURE_STORAGE_CONNECTION_STRING="DefaultEndpointsProtocol=https;AccountName=your-account;AccountKey=your-key;EndpointSuffix=core.windows.net"

# Optional container names (defaults provided)
AZURE_STORAGE_CONTAINER_NAME_SOURCE="source"
AZURE_STORAGE_CONTAINER_NAME_TARGET="target"

# Required for translation service
AZURE_TRANSLATION_KEY="your-translation-api-key"
AZURE_TRANSLATION_ENDPOINT="https://your-region.cognitiveservices.azure.com"

# Optional translation URIs (defaults provided)
AZURE_TRANSLATION_SOURCE_URI="https://your-storage.blob.core.windows.net/source"
AZURE_TRANSLATION_TARGET_URI="https://your-storage.blob.core.windows.net/target"
```

## Testing in Different Environments

### Local Development
```bash
cd d:\work\202506_BabelScrib\babelscrib
python manage.py runserver
# Visit http://localhost:8000/test-azure-storage/
```

### Production Deployment
1. Deploy your application with the enhanced code
2. Set all required environment variables
3. Visit `https://your-domain.com/test-azure-storage/`
4. Run the test to validate configuration

### CI/CD Integration
You can also call the test endpoint programmatically:

```bash
# JSON API call for automated testing
curl -H "Content-Type: application/json" https://your-domain.com/test-azure-storage/
```

## File Upload Error Resolution

When you encounter "Storage configuration invalid" during file upload:

1. **Immediate Action**: Visit `/test-azure-storage/` to get detailed diagnostics
2. **Check Results**: Look for specific failed operations
3. **Fix Issues**: Address the specific problems identified
4. **Retry Upload**: Try uploading the file again

## Implementation Details

### Enhanced Functions Added

1. **`test_azure_storage(request)`**: Main test endpoint
2. **`test_container_operations(blob_service_client, container_name, container_type)`**: Container-specific tests
3. **`test_blob_crud_operations(blob_service_client, container_name)`**: Blob operation tests
4. **`test_translation_service_config()`**: Translation service validation
5. **`debug_connection_string(connection_string)`**: Enhanced with better error reporting

### Enhanced Error Messages

All storage operations now provide:
- Specific error descriptions
- Troubleshooting guidance
- Reference to the test endpoint

### URL Routes Added

- `/test-azure-storage/` - Storage test interface and API
- Enhanced error responses in existing endpoints

## Security Considerations

- Test operations use temporary, timestamped blob names
- All test blobs are automatically cleaned up
- Connection string validation doesn't log sensitive data
- Test results don't expose connection string contents

## Next Steps

1. **Deploy Enhanced Code**: Deploy this updated version to production
2. **Run Storage Test**: Execute the test in production environment
3. **Fix Identified Issues**: Address any problems found by the test
4. **Verify File Upload**: Test the original file upload functionality
5. **Monitor Logs**: Use the enhanced error messages for ongoing troubleshooting

This comprehensive testing system will help you quickly identify and resolve any Azure Storage configuration issues in production.
