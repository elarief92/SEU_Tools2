from django.contrib import admin
from django.utils.html import format_html
from .models import CertificateUpload, APIEndpoint


@admin.register(CertificateUpload)
class CertificateUploadAdmin(admin.ModelAdmin):
    """Admin configuration for CertificateUpload model."""
    list_display = ['user', 'processing_type', 'status', 'file_size_formatted', 'created_at']
    list_filter = ['status', 'processing_type', 'created_at']
    search_fields = ['filename', 'user__username']
    ordering = ['-created_at']
    
    fieldsets = (
        ('File Info', {
            'fields': ('user', 'file', 'filename', 'file_size')
        }),
        ('Processing Info', {
            'fields': ('processing_type', 'status', 'processing_time', 'result')
        }),
        ('Error Info', {
            'fields': ('error_message',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def file_size_formatted(self, obj):
        """Format file size in human readable format."""
        if obj.file_size < 1024:
            return f"{obj.file_size} B"
        elif obj.file_size < 1024 * 1024:
            return f"{obj.file_size / 1024:.1f} KB"
        else:
            return f"{obj.file_size / (1024 * 1024):.1f} MB"
    
    file_size_formatted.short_description = 'File Size'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(APIEndpoint)
class APIEndpointAdmin(admin.ModelAdmin):
    """Admin configuration for APIEndpoint model."""
    list_display = ['endpoint', 'total_calls', 'successful_calls', 'failed_calls', 'success_rate', 'avg_response_time', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['endpoint', 'description']
    ordering = ['endpoint']
    
    fieldsets = (
        ('Endpoint Info', {
            'fields': ('endpoint', 'description', 'is_active')
        }),
        ('Statistics', {
            'fields': ('total_calls', 'successful_calls', 'failed_calls', 'avg_response_time')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']
    
    def success_rate(self, obj):
        """Display success rate as percentage."""
        rate = obj.get_success_rate()
        if rate >= 95:
            color = 'green'
        elif rate >= 80:
            color = 'orange'
        else:
            color = 'red'
        return format_html(
            '<span style="color: {};">{:.1f}%</span>',
            color,
            rate
        )
    
    success_rate.short_description = 'Success Rate'
