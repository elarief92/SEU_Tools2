from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from .models import User, APIToken, ProcessingHistory


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin configuration for User model."""
    list_display = ['username', 'email', 'is_admin', 'is_active', 'is_staff', 'created_at']
    list_filter = ['is_admin', 'is_active', 'is_staff', 'is_superuser', 'created_at']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['-created_at']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('is_admin', 'created_at', 'updated_at'),
        }),
    )
    
    readonly_fields = ['created_at', 'updated_at']


@admin.register(APIToken)
class APITokenAdmin(admin.ModelAdmin):
    """Admin configuration for APIToken model."""
    list_display = ['name', 'user', 'is_active', 'expires_at', 'last_used', 'created_at']
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['name', 'user__username', 'token']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Token Info', {
            'fields': ('user', 'name', 'token', 'is_active')
        }),
        ('Timestamps', {
            'fields': ('expires_at', 'last_used', 'created_at')
        }),
    )
    
    readonly_fields = ['token', 'created_at', 'last_used']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')


@admin.register(ProcessingHistory)
class ProcessingHistoryAdmin(admin.ModelAdmin):
    """Admin configuration for ProcessingHistory model."""
    list_display = ['user', 'endpoint', 'status', 'processing_time', 'created_at']
    list_filter = ['status', 'endpoint', 'created_at']
    search_fields = ['user__username', 'endpoint']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Request Info', {
            'fields': ('user', 'endpoint', 'status', 'processing_time', 'result')
        }),
        ('Error Info', {
            'fields': ('error_message',)
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )
    
    readonly_fields = ['created_at']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
