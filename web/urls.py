"""
URL configuration for web app.
"""
from django.urls import path
from . import views

app_name = 'web'

urlpatterns = [
    path('', views.DashboardView.as_view(), name='dashboard'),
    path('login/', views.LoginPageView.as_view(), name='login'),
    path('logout/', views.LogoutPageView.as_view(), name='logout'),
    path('process/', views.ProcessView.as_view(), name='process'),
    path('process/upload/', views.ProcessUploadView.as_view(), name='process_upload'),
    path('tokens/', views.TokensView.as_view(), name='tokens'),
    path('tokens/create/', views.TokenCreateView.as_view(), name='token_create'),
    path('tokens/<int:pk>/revoke/', views.TokenRevokeView.as_view(), name='token_revoke'),
    path('history/', views.HistoryView.as_view(), name='history'),
    path('history/<int:pk>/download/', views.HistoryDownloadView.as_view(), name='history_download'),
    path('history/export/', views.HistoryExportView.as_view(), name='history_export'),
    path('api-requests/', views.APIRequestListView.as_view(), name='api_requests'),
    path('api-requests/create/', views.APIRequestCreateView.as_view(), name='api_request_create'),
    path('api-requests/<int:pk>/', views.APIRequestDetailView.as_view(), name='api_request_detail'),
    path('api-requests/<int:pk>/json/', views.APIRequestDetailView.as_view(), name='api_request_detail_json'),
    path('api-requests/<int:pk>/update/', views.APIRequestUpdateView.as_view(), name='api_request_update'),
] 