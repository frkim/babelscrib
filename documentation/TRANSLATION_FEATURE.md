# Translation Feature Documentation

## Overview

The BabelScrib application now includes an integrated document translation feature that allows users to translate uploaded documents using Azure Cognitive Services Document Translation API.

## How It Works

1. **Upload Documents**: Users upload their documents through the existing upload interface
2. **Upload Complete**: When uploads are successful, a "Launch Translation Process" button appears
3. **Select Languages**: Users can choose source and target languages for translation
4. **Start Translation**: Click the button to initiate the translation process
5. **View Results**: Translation status and results are displayed in real-time

## User Interface

### Upload Interface
- Drag and drop or select files (PDF, DOCX, PPTX, TXT, MD)
- Enter email address
- Upload files to Azure Storage

### Translation Controls (appears after successful upload)
- **Target Language Dropdown**: Select the language to translate to
- **Source Language Dropdown**: Specify source language or use auto-detect
- **Launch Translation Process Button**: Starts the translation
- **Translation Status**: Shows progress and results

### Supported Languages
- English (en)
- Spanish (es)  
- French (fr)
- German (de)
- Italian (it)
- Portuguese (pt)
- Polish (pl)

## Technical Implementation

### Backend Components

1. **Translation Service Library** (`lib/translation_service.py`)
   - `DocumentTranslationService` class for Azure API integration
   - Error handling and logging
   - Structured JSON responses

2. **Configuration Management** (`lib/config.py`)
   - Environment variable support
   - Django settings integration
   - Validation and error handling

3. **Django Views** (`upload/views.py`)
   - `translate_documents()` view for handling translation requests
   - JSON API endpoint at `/translate/`
   - Email validation and error handling

### Frontend Components

1. **HTML Template** (`upload/templates/upload/index.html`)
   - Translation controls section
   - Language selection dropdowns
   - Status display areas

2. **JavaScript** (`static/js/upload.js`)
   - Show translation controls after successful upload
   - Handle translation button click
   - AJAX request to translation endpoint
   - Display translation status and results

### API Endpoints

#### POST /translate/
Initiates document translation process.

**Request Body:**
```json
{
    "target_language": "en",
    "source_language": "es",  // optional
    "email": "user@example.com"
}
```

**Response (Success):**
```json
{
    "success": true,
    "data": {
        "status": "Succeeded",
        "created_on": "2025-06-06T10:00:00Z",
        "total_documents": 2,
        "succeeded_documents": 2,
        "failed_documents": 0,
        "documents": [
            {
                "id": "doc1",
                "status": "Succeeded",
                "source_document_url": "https://...",
                "translated_document_url": "https://...",
                "translated_to": "en",
                "error": null
            }
        ]
    },
    "message": "Translation started successfully. Status: Succeeded"
}
```

**Response (Error):**
```json
{
    "error": "Translation failed: API key not configured"
}
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# Azure Translation Service
AZURE_TRANSLATION_KEY=your_azure_translation_key
AZURE_TRANSLATION_ENDPOINT=https://yourservice.cognitiveservices.azure.com
AZURE_TRANSLATION_SOURCE_URI=https://yourstorage.blob.core.windows.net/source
AZURE_TRANSLATION_TARGET_URI=https://yourstorage.blob.core.windows.net/target

# Azure Storage (for uploads)
AZURE_STORAGE_CONNECTION_STRING=your_connection_string
AZURE_STORAGE_CONTAINER_NAME_SOURCE=source
AZURE_STORAGE_CONTAINER_NAME_TARGET=target
```

### Django Settings (Alternative)

Add to your `settings.py`:

```python
# Azure Translation Service Settings
AZURE_TRANSLATION_KEY = 'your_azure_translation_key'
AZURE_TRANSLATION_ENDPOINT = 'https://yourservice.cognitiveservices.azure.com'
AZURE_TRANSLATION_SOURCE_URI = 'https://yourstorage.blob.core.windows.net/source'
AZURE_TRANSLATION_TARGET_URI = 'https://yourstorage.blob.core.windows.net/target'
```

## Error Handling

The system includes comprehensive error handling:

1. **Configuration Errors**: Missing API keys or endpoints
2. **Network Errors**: Azure service unavailability
3. **Validation Errors**: Invalid email or language codes
4. **Translation Errors**: Document processing failures

Errors are logged and displayed to users with helpful messages.

## Usage Flow

1. User uploads documents successfully
2. Translation controls appear automatically
3. User selects target language (source language is optional)
4. User clicks "Launch Translation Process"
5. System validates request and starts translation
6. Real-time status updates are shown
7. Completion status with document details is displayed

## Security Considerations

- API keys are stored in environment variables, not in code
- Email validation prevents injection attacks
- CSRF protection on Django views
- Error messages don't expose sensitive information

## Future Enhancements

- **Progress Tracking**: Long-running translation status polling
- **Email Notifications**: Send translation completion emails
- **Batch Processing**: Handle large document sets
- **Download Links**: Direct download of translated documents
- **Translation History**: Track previous translations per user
