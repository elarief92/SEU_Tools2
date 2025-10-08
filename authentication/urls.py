"""
URL configuration for authentication app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'authentication'

# DRF Router for API endpoints
router = DefaultRouter()
router.register(r'users', views.UserViewSet, basename='user')
router.register(r'tokens', views.APITokenViewSet, basename='token')

urlpatterns = [
    # JWT Token endpoint (primary API authentication)
    path('token/', views.TokenCreateView.as_view(), name='token_create'),
    
    # Authentication views
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('register/', views.RegisterView.as_view(), name='register'),
    
    # Session authentication for browsable API
    path('session-login/', views.SessionLoginView.as_view(), name='session_login'),
    path('session-logout/', views.SessionLogoutView.as_view(), name='session_logout'),
    
    # API Token management
    path('api/token/', views.APITokenCreateView.as_view(), name='api_token_create'),
    path('api/token/refresh/', views.APITokenRefreshView.as_view(), name='api_token_refresh'),
    path('api/token/revoke/', views.APITokenRevokeView.as_view(), name='api_token_revoke'),
    
    # User management API
    path('api/', include(router.urls)),

] 