from rest_framework import serializers
from .models import CertificateUpload, APIEndpoint


class APIEndpointSerializer(serializers.ModelSerializer):
    """Serializer for APIEndpoint model."""
    success_rate = serializers.ReadOnlyField(source='get_success_rate')
    
    class Meta:
        model = APIEndpoint
        fields = ['id', 'endpoint', 'description', 'total_calls', 'successful_calls', 'failed_calls', 'success_rate', 'avg_response_time', 'is_active', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at'] 