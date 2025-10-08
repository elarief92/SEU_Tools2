from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from datetime import datetime, timedelta
import secrets


class User(AbstractUser):
    """Extended User model with additional fields."""
    email = models.EmailField(unique=True, null=True, blank=True)
    is_admin = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return self.username


class APIToken(models.Model):
    """API Token model for API authentication."""
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='api_tokens')
    token = models.CharField(max_length=255, unique=True, db_index=True)
    name = models.CharField(max_length=100, help_text="Token name/description")
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'tokens'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = secrets.token_urlsafe(32)
        super().save(*args, **kwargs)
    
    def is_expired(self):
        """Check if token is expired."""
        from django.utils import timezone
        return timezone.now() > self.expires_at if self.expires_at else False
    
    def update_last_used(self):
        """Update last used timestamp."""
        from django.utils import timezone
        self.last_used = timezone.now()
        self.save(update_fields=['last_used'])


class ProcessingHistory(models.Model):
    """Model to track API request processing history."""
    STATUS_CHOICES = [
        ('success', 'Success'),
        ('error', 'Error'),
        ('processing', 'Processing'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='processing_history')
    requester = models.CharField(max_length=100, null=True, blank=True, help_text="Token name that made the request")
    endpoint = models.CharField(max_length=100, help_text="Which endpoint was used")
    processing_time = models.CharField(max_length=10, null=True, blank=True, help_text="Processing time in seconds")
    result = models.TextField(null=True, blank=True, help_text="JSON result")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='success')
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'processing_history'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.endpoint} - {self.status}"
