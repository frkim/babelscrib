from django.db import models
import hashlib

class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    user_email = models.EmailField(default='')
    user_id_hash = models.CharField(max_length=64, db_index=True, default='')
    blob_name = models.CharField(max_length=500)  # Original filename
    user_blob_name = models.CharField(max_length=500, default='')  # User-specific blob name
    is_translated = models.BooleanField(default=False)
    translation_language = models.CharField(max_length=10, blank=True, null=True)
    
    def __str__(self):
        return f"{self.title} - {self.user_email}"
    
    class Meta:
        indexes = [
            models.Index(fields=['user_email', 'uploaded_at']),
            models.Index(fields=['user_id_hash']),
        ]

class UserSession(models.Model):
    session_key = models.CharField(max_length=40, unique=True)
    user_email = models.EmailField()
    user_id_hash = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Session for {self.user_email}"
    
    @staticmethod
    def create_user_hash(email):
        """Create a hash from user email for folder naming."""
        return hashlib.sha256(email.encode()).hexdigest()[:16]
    
    @staticmethod
    def cleanup_old_sessions(hours=24):
        """Clean up sessions older than specified hours."""
        from django.utils import timezone
        import datetime
        cutoff_time = timezone.now() - datetime.timedelta(hours=hours)
        old_sessions = UserSession.objects.filter(last_activity__lt=cutoff_time)
        count = old_sessions.count()
        old_sessions.delete()
        return count
    
    class Meta:
        indexes = [
            models.Index(fields=['session_key']),
            models.Index(fields=['user_email']),
        ]