"""
URL configuration for APIs app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    APIEndpointViewSet,
    ExtractSubscriptionMonthsView,
    ExtractSubscriptionMonthsByAIView,
    GetStudentTranscriptView,
    StudentInfoView,
    api_root,
    process_certificate
)

# Create DRF router
router = DefaultRouter()
router.register(r'endpoints', APIEndpointViewSet, basename='endpoint')

urlpatterns = [
    # API root (custom view with anonymous access)
    path('', api_root, name='api-root'),
    
    # Certificate processing endpoints
    path('extract-GOSI_subscription/', ExtractSubscriptionMonthsView.as_view(), name='extract-GOSI_subscription'),
    path('AI_extract-GOSI_subscription/', ExtractSubscriptionMonthsByAIView.as_view(), name='AI_extract-GOSI_subscription'),
    
    # Student services endpoints
    path('get-student-transcript/', GetStudentTranscriptView.as_view(), name='get-student-transcript'),
    path('student-info/', StudentInfoView.as_view(), name='student-info'),
    
    # Web interface compatibility endpoint
    path('process-certificate/', process_certificate, name='process-certificate'),
    
    # DRF router endpoints (endpoints only, not root)
    path('', include(router.urls)),
] 