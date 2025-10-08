"""
Swagger/OpenAPI configuration for SEU Tools API.
"""
from django.urls import path, include
from drf_yasg import openapi
from drf_yasg.views import get_schema_view
from rest_framework import permissions
from apis.views import ExtractSubscriptionMonthsView, ExtractSubscriptionMonthsByAIView, GetStudentTranscriptView

# Custom URL patterns for Swagger (only the endpoints we want to document)
swagger_urlpatterns = [
    path('extract-GOSI_subscription/', ExtractSubscriptionMonthsView.as_view(), name='extract-GOSI_subscription'),
    path('AI_extract-GOSI_subscription/', ExtractSubscriptionMonthsByAIView.as_view(), name='AI_extract-GOSI_subscription'),
    path('get-student-transcript/', GetStudentTranscriptView.as_view(), name='get-student-transcript'),
]

# API Information
schema_view = get_schema_view(
    openapi.Info(
        title="SEU Tools API",
        default_version='v1',
        description="""
        
        ## Authentication
        
        This API uses token-based authentication. To access protected endpoints, you need to:
        
        1. Obtain an API token from the system administrator
        2. Include the token in the Authorization header: `Authorization: Bearer YOUR_TOKEN`
        
        ## Available Endpoints
        
        This API provides two main endpoints for processing GOSI certificates:
        
        - **extract-GOSI_subscription**: Standard PDF text extraction
        - **AI_extract-GOSI_subscription**: AI-powered analysis for complex certificates
        """,
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
    patterns=[
        # Only include the specific endpoints we want in Swagger
        path('api/v1/', include(swagger_urlpatterns)),
    ],
) 