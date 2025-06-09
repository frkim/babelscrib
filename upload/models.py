from django.db import models
import hashlib

class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # User identification and ownership
    user_email = models.EmailField()  # Store user email
    user_id_hash = models.CharField(max_length=64, db_index=True)  # Hashed email for privacy
    # File tracking for Azure storage
    blob_name = models.CharField(max_length=500)  # Original filename in Azure
    user_blob_name = models.CharField(max_length=500)  # User-specific blob name
    is_translated = models.BooleanField(default=False)
    translation_language = models.CharField(max_length=10, blank=True, null=True)
    
    def save(self, *args, **kwargs):
        # Generate user ID hash from email for privacy
        if self.user_email and not self.user_id_hash:
            self.user_id_hash = hashlib.sha256(self.user_email.lower().encode()).hexdigest()[:16]
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.title} ({self.user_email})"
    
    class Meta:
        indexes = [
            models.Index(fields=['user_email', 'uploaded_at']),
            models.Index(fields=['user_id_hash']),
        ]

class UserSession(models.Model):
    """Track user sessions for temporary access control"""
    session_key = models.CharField(max_length=40, unique=True)
    user_email = models.EmailField()
    user_id_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if self.user_email and not self.user_id_hash:
            self.user_id_hash = hashlib.sha256(self.user_email.lower().encode()).hexdigest()[:16]
        super().save(*args, **kwargs)
    
    class Meta:
        indexes = [
            models.Index(fields=['session_key']),
            models.Index(fields=['user_email']),
        ]