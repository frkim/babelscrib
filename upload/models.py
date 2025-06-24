from django.db import models

class Document(models.Model):
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    # File tracking for Azure storage
    blob_name = models.CharField(max_length=500)  # Original filename in Azure
    is_translated = models.BooleanField(default=False)
    translation_language = models.CharField(max_length=10, blank=True, null=True)
    
    def __str__(self):
        return f"{self.title}"
    
    class Meta:
        indexes = [
            models.Index(fields=['uploaded_at']),
        ]