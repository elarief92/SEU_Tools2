"""
URL configuration for seu_tools project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from .swagger import schema_view

# Non-internationalized URLs (API, admin, media)
urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    path('swagger.json', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger.yaml', schema_view.without_ui(cache_timeout=0), name='schema-yaml'),
    
    # API v1 routes (not internationalized)
    path('api/v1/', include('apis.urls')),
    
    # Authentication API v1 routes (not internationalized)
   # path('api/v1/auth/', include(('authentication.urls', 'auth_api'), namespace='auth_api')),
    
    # Language switching
    path('set_language/', include('django.conf.urls.i18n')),
]

# Internationalized URLs (web interface)
urlpatterns += i18n_patterns(
    # Authentication routes (web interface)
    path('auth/', include(('authentication.urls', 'auth_web'), namespace='auth_web')),
    
    # Web interface
    path('', include('web.urls')),
    
    prefix_default_language=False,  # Don't prefix default language (English)
)

# Static and Media files
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Admin site customization
admin.site.site_header = "SEU Tools Administration"
admin.site.site_title = "SEU Tools Admin"
admin.site.index_title = "Welcome to SEU Tools Administration"
