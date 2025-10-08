from django.db import models
from django.conf import settings
from django.utils import timezone

# Create your models here.

class APIEndpointRequest(models.Model):
    """Model for requesting new API endpoints."""
    HTTP_METHOD_CHOICES = [
        ('GET', 'GET'),
        ('POST', 'POST'),
        ('PUT', 'PUT'),
        ('PATCH', 'PATCH'),
        ('DELETE', 'DELETE')
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected')
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='endpoint_requests')
    requester = models.CharField(max_length=100, null=True, blank=True, help_text="Who made the request")
    title = models.CharField(max_length=200, help_text="Brief title for the API endpoint")
    description = models.TextField(help_text="Detailed description of what this endpoint should do")
    endpoint_path = models.CharField(max_length=100, blank=True, help_text="Suggested endpoint path (e.g., /api/v1/new-feature/)")
    http_method = models.CharField(max_length=10, choices=HTTP_METHOD_CHOICES, default='POST', help_text="Expected HTTP method")
    expected_input = models.TextField(help_text="Description of expected input data/parameters")
    expected_output = models.TextField(help_text="Description of expected output/response format")
    business_justification = models.TextField(blank=True, help_text="Why is this endpoint needed? What business problem does it solve?")
    use_case = models.TextField(blank=True, help_text="How will this endpoint be used? Provide specific examples.")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', help_text="Priority level for this request")
    date_needed = models.DateField(help_text="When do you need this endpoint to be available?")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(blank=True, help_text="Internal notes from admin/development team")
    developed_endpoint_url = models.URLField(null=True, blank=True, help_text="The actual endpoint URL after development is complete")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'API Endpoint Request'
        verbose_name_plural = 'API Endpoint Requests'
        ordering = ['-created_at']
        db_table = 'api_endpoint_requests'  # Use the existing table name
    
    def __str__(self):
        return f"{self.title} ({self.status})"
