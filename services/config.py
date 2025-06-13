"""
Configuration management for the Document Translation Service.

This module handles configuration loading from environment variables and settings files.
"""

import os
from typing import Optional
from django.conf import settings as django_settings


class TranslationConfig:
    """Configuration class for document translation service."""
    
    def __init__(self):
        self._key: Optional[str] = None
        self._endpoint: Optional[str] = None
        self._source_uri: Optional[str] = None
        self._target_uri: Optional[str] = None
    
    @property
    def key(self) -> str:
        """Get Azure Cognitive Services API key."""
        if self._key:
            return self._key
        
        # Try Django settings first
        if hasattr(django_settings, 'AZURE_TRANSLATION_KEY'):
            return django_settings.AZURE_TRANSLATION_KEY
          # Try environment variable
        key = os.getenv('AZURE_TRANSLATION_KEY')
        if key:
            return key
        
        # If no key is found, raise an error instead of using hardcoded key
        raise ValueError(
            "Azure Translation API key not found. Please set AZURE_TRANSLATION_KEY environment variable "
            "or configure AZURE_TRANSLATION_KEY in Django settings."
        )

    
    @key.setter
    def key(self, value: str):
        """Set Azure Cognitive Services API key."""
        self._key = value
    
    @property
    def endpoint(self) -> str:
        """Get Azure Cognitive Services endpoint."""
        if self._endpoint:
            return self._endpoint
        
        # Try Django settings first
        if hasattr(django_settings, 'AZURE_TRANSLATION_ENDPOINT'):
            return django_settings.AZURE_TRANSLATION_ENDPOINT
        
        # Try environment variable
        endpoint = os.getenv('AZURE_TRANSLATION_ENDPOINT')
        if endpoint:
            return endpoint
        
        # Fallback to hardcoded value
        return 'https://babelscrib.cognitiveservices.azure.com'
    
    @endpoint.setter
    def endpoint(self, value: str):
        """Set Azure Cognitive Services endpoint."""
        self._endpoint = value
    
    @property
    def source_uri(self) -> str:
        """Get default source container URI."""
        if self._source_uri:
            return self._source_uri
        
        # Try Django settings first
        if hasattr(django_settings, 'AZURE_TRANSLATION_SOURCE_URI'):
            return django_settings.AZURE_TRANSLATION_SOURCE_URI
        
        # Try environment variable
        source_uri = os.getenv('AZURE_TRANSLATION_SOURCE_URI')
        if source_uri:
            return source_uri
        
        # Fallback to hardcoded value
        return 'https://babelscribdocs.blob.core.windows.net/source'
    
    @source_uri.setter
    def source_uri(self, value: str):
        """Set default source container URI."""
        self._source_uri = value
    
    @property
    def target_uri(self) -> str:
        """Get default target container URI."""
        if self._target_uri:
            return self._target_uri
        
        # Try Django settings first
        if hasattr(django_settings, 'AZURE_TRANSLATION_TARGET_URI'):
            return django_settings.AZURE_TRANSLATION_TARGET_URI
        
        # Try environment variable
        target_uri = os.getenv('AZURE_TRANSLATION_TARGET_URI')
        if target_uri:
            return target_uri
        
        # Fallback to hardcoded value
        return 'https://babelscribdocs.blob.core.windows.net/target'
    
    @target_uri.setter
    def target_uri(self, value: str):
        """Set default target container URI."""
        self._target_uri = value


# Global configuration instance
config = TranslationConfig()


def get_config() -> TranslationConfig:
    """Get the global configuration instance."""
    return config
