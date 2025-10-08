from rest_framework import serializers
from .models import User, APIToken, ProcessingHistory


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model."""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'is_admin', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class APITokenSerializer(serializers.ModelSerializer):
    """Serializer for APIToken model."""
    class Meta:
        model = APIToken
        fields = ['id', 'token', 'name', 'expires_at', 'is_active', 'created_at', 'last_used']
        read_only_fields = ['id', 'token', 'created_at', 'last_used']


class ProcessingHistorySerializer(serializers.ModelSerializer):
    """Serializer for ProcessingHistory model."""
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = ProcessingHistory
        fields = ['id', 'user', 'endpoint', 'filename', 'file_type', 'file_size', 'processing_time', 'result', 'status', 'error_message', 'created_at']
        read_only_fields = ['id', 'created_at'] 