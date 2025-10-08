# SEU Tools - Architecture Documentation

## Overview
SEU Tools is a Django-based certificate processing system that extracts and analyzes data from certificates. The system was recently migrated from FastAPI to Django to provide better web interface capabilities and leverage Django's built-in features.

## Architecture Principles

### 1. Model-First Development
All new features start with the model layer:
- **Data Structure**: Define models with proper fields and constraints
- **Business Logic**: Implement methods and properties on models
- **Relationships**: Use Django's ORM relationship fields
- **Validation**: Add model-level validation

### 2. No Internal API Endpoints
- Web app features use Django template context
- API endpoints are ONLY for external consumers
- No AJAX calls to internal APIs for web functionality
- Data flows through Django's MVT pattern

### 3. Clear Separation of Concerns

```
┌─────────────────┐    ┌─────────────────┐
│   External      │    │   Web App       │
│   Consumers     │    │   Users         │
└─────────────────┘    └─────────────────┘
         │                       │
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌─────────────────┐
│   apis/         │    │   web/          │
│   (DRF Views)   │    │   (Templates)   │
└─────────────────┘    └─────────────────┘
         │                       │
         │                       │
         └───────────┬───────────┘
                     │
                     ▼
            ┌─────────────────┐
            │   Models        │
            │   (Data Layer)  │
            └─────────────────┘
```

## Project Structure

```
SEU_Tools/
├── apis/                    # External API endpoints
│   ├── models.py           # API-specific models
│   ├── serializers.py      # DRF serializers
│   ├── views.py            # API views
│   └── urls.py             # API URL patterns
├── web/                     # Web application
│   ├── views.py            # Web views (template-based)
│   ├── urls.py             # Web URL patterns
│   └── forms.py            # Django forms
├── authentication/          # User management
│   ├── models.py           # User, Token models
│   ├── views.py            # Auth views
│   └── serializers.py      # Auth serializers
├── templates/              # HTML templates
│   ├── base.html           # Base template
│   ├── web/                # Web app templates
│   └── authentication/     # Auth templates
├── static/                 # Static files
│   ├── css/                # Stylesheets
│   ├── js/                 # JavaScript
│   └── images/             # Images
└── seu_tools/              # Django project
    ├── settings.py         # Configuration
    ├── urls.py             # Root URLs
    └── wsgi.py             # WSGI config
```

## Data Flow Patterns

### Web App Feature Implementation
1. **Model**: Create/update model with business logic
2. **View**: Class-based view with context preparation
3. **Template**: Bootstrap 5 template with proper UI

```python
# Example: Token Statistics
class TokensView(LoginRequiredMixin, TemplateView):
    template_name = 'tokens.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_tokens = self.request.user.tokens.all()
        
        # Calculate stats in view, pass via context
        context['token_stats'] = {
            'active': user_tokens.filter(
                is_active=True,
                expires_at__gt=timezone.now()
            ).count(),
            'total': user_tokens.count(),
        }
        return context
```

### API Feature Implementation
1. **Model**: Same as web app
2. **Serializer**: DRF serializer for JSON response
3. **View**: DRF view with proper authentication

```python
# Example: External API endpoint
class TokenListAPIView(ListAPIView):
    serializer_class = TokenSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return self.request.user.tokens.all()
```

## Key Components

### Authentication System
- **Session-based**: For web app users
- **Token-based**: For API consumers
- **Role-based**: Admin, regular users
- **Security**: CSRF protection, proper validation

### Certificate Processing
- **Upload**: File handling and validation
- **Processing**: Data extraction algorithms
- **Storage**: Processed data storage
- **History**: Audit trail of all operations

### User Interface
- **Bootstrap 5**: Responsive design
- **Progressive Enhancement**: Works without JavaScript
- **Accessibility**: WCAG compliant
- **Mobile-first**: Responsive layouts

## Database Design

### Core Models
- **User**: Extended Django user model
- **Token**: API authentication tokens
- **ProcessingHistory**: Certificate processing records
- **CertificateData**: Extracted certificate information

### Relationships
```
User (1) ──────── (Many) Token
 │
 └─ (1) ──────── (Many) ProcessingHistory
                    │
                    └─ (1) ──────── (1) CertificateData
```

## Security Considerations

### Web App Security
- CSRF protection on all forms
- XSS prevention in templates
- Proper input validation
- Session security

### API Security
- Token-based authentication
- Rate limiting
- Input validation
- Proper error handling

## Performance Optimization

### Database
- Proper indexing on frequently queried fields
- Use select_related() and prefetch_related()
- Database connection pooling
- Query optimization

### Frontend
- Static file compression
- Browser caching headers
- Minimal JavaScript usage
- Optimized images

## Testing Strategy

### Unit Tests
- Model methods and properties
- View logic and context
- Form validation
- Utility functions

### Integration Tests
- Full request/response cycles
- Authentication flows
- File upload processing
- API endpoint testing

## Deployment Architecture

### Development
- SQLite database
- Django development server
- Debug mode enabled
- Local file storage

### Production
- PostgreSQL database
- WSGI server (Gunicorn)
- Reverse proxy (Nginx)
- Static file serving
- SSL/TLS encryption

## Migration Strategy

### From FastAPI to Django
- ✅ Preserve existing API endpoints
- ✅ Maintain data compatibility
- ✅ Add web interface capabilities
- ✅ Improve admin functionality

### Future Considerations
- Microservices architecture
- Container deployment
- Cloud storage integration
- Advanced analytics

## Development Workflow

1. **Feature Planning**: Understand requirements
2. **Model Design**: Create data structures
3. **View Implementation**: Handle business logic
4. **Template Creation**: Build user interface
5. **Testing**: Verify functionality
6. **Documentation**: Update relevant docs
7. **Deployment**: Follow deployment procedures

## Best Practices Summary

### DO:
- Start with models
- Use Django's built-in features
- Follow MVT pattern
- Implement proper security
- Write comprehensive tests

### DON'T:
- Create internal API endpoints for web app
- Put business logic in templates
- Bypass Django's security features
- Ignore database optimization
- Skip documentation

This architecture ensures maintainability, security, and scalability while leveraging Django's strengths. 