# Services

This directory contains the core business logic and services for the BabelScrib document translation application.

## Files

- **`translation_service.py`**: Core document translation service using Azure Cognitive Services
- **`config.py`**: Configuration management for translation services
- **`__init__.py`**: Package initialization

## Usage

```python
# Import the translation service
from services.translation_service import create_translation_service
from services.config import get_config

# Get configuration
config = get_config()

# Create translation service
translation_service = create_translation_service(config.key, config.endpoint)

# Translate documents
result = translation_service.translate_documents(
    source_uri="https://...",
    target_uri="https://...",
    target_language="en"
)
```

## Migration from lib/

This directory replaces the previous `lib/` directory. All imports have been updated from:
- `from lib.translation_service import ...` → `from services.translation_service import ...`
- `from lib.config import ...` → `from services.config import ...`
