from django.db import models
from django.conf import settings
from django.core.files.storage import default_storage
import os


class CertificateUpload(models.Model):
    """Model to track certificate uploads and processing."""
    PROCESSING_TYPE_CHOICES = [
        ('standard', 'Standard Processing'),
        ('ai', 'AI Processing'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='certificate_uploads')
    file = models.FileField(upload_to='certificates/', max_length=255)
    filename = models.CharField(max_length=255)
    file_size = models.IntegerField()
    processing_type = models.CharField(max_length=20, choices=PROCESSING_TYPE_CHOICES, default='standard')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    result = models.TextField(null=True, blank=True, help_text="Processing result")
    error_message = models.TextField(null=True, blank=True)
    processing_time = models.DurationField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.filename}"
    
    def delete(self, *args, **kwargs):
        """Delete the file when the model instance is deleted."""
        if self.file:
            if default_storage.exists(self.file.name):
                default_storage.delete(self.file.name)
        super().delete(*args, **kwargs)



class APIEndpoint(models.Model):
    """Model to track API endpoint usage statistics."""
    endpoint = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    total_calls = models.IntegerField(default=0)
    successful_calls = models.IntegerField(default=0)
    failed_calls = models.IntegerField(default=0)
    avg_response_time = models.FloatField(default=0.0, help_text="Average response time in seconds")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['endpoint']
    
    def __str__(self):
        return self.endpoint
    
    def get_success_rate(self):
        """Calculate success rate percentage."""
        if self.total_calls == 0:
            return 0
        return (self.successful_calls / self.total_calls) * 100
