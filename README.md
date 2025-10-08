# SEU Tools - General API Platform

## Overview
SEU Tools is a Django-based API platform that provides certificate processing services using AI and standard text extraction methods. The platform serves as a general-purpose API gateway with unified authentication and monitoring.

## Features

### 🔧 Web Interface
- **Dashboard**: Real-time analytics and processing statistics
- **Certificate Processing**: Upload and process GOSI certificates
- **API Token Management**: Create and manage API tokens
- **Processing History**: View and export processing results
- **Admin Panel**: User and system management

### 🚀 API Endpoints
- **Certificate Processing (Standard)**: Extract subscription months using text processing
- **Certificate Processing (AI)**: Extract subscription months using AI analysis
- **History & Analytics**: Access processing history and download results
- **Authentication**: JWT token-based authentication
- **Documentation**: Complete API documentation with OpenAPI/Swagger

### 📱 Dynamic APIs Navigation
The web interface now includes a dynamic **APIs** dropdown menu that provides:
- **Organized API Categories**: Certificate Processing, History & Analytics, Authentication, Documentation
- **Direct Testing Links**: Click to open API endpoints in new tabs
- **HTTP Method Badges**: Visual indicators for GET, POST methods
- **Search Functionality**: Search through available APIs
- **Copy to Clipboard**: Right-click or double-click to copy endpoint URLs
- **Keyboard Shortcuts**: Ctrl+Shift+A to open API dropdown

## Quick Start

### Prerequisites
- Python 3.8+
- Django 4.2+
- SQLite (default) or PostgreSQL/MySQL

### Installation
   ```bash
# Clone the repository
   git clone <repository-url>
cd SEU_Tools

# Create virtual environment
   python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
   pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Testing the APIs
1. **Web Interface**: Navigate to `http://localhost:8000`
2. **Login**: Use your credentials to access the dashboard
3. **APIs Menu**: Click on the "APIs" dropdown in the navigation
4. **Test Endpoints**: Click on any API endpoint to test it directly
5. **API Documentation**: Visit `/docs/` or `/redoc/` for complete API documentation

### API Testing Examples
   ```bash
# Get API root information
curl http://localhost:8000/api/v1/

# Login and get token
curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username": "your_username", "password": "your_password"}'

# Process certificate (requires authentication)
curl -X POST http://localhost:8000/api/v1/extract-GOSI_subscription/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@certificate.pdf"

# Get processing history
curl http://localhost:8000/api/v1/history/ \
  -H "Authorization: Bearer YOUR_TOKEN"
   ```

## Architecture

### Platform Design
- **General-Purpose Gateway**: Designed to handle multiple backend systems
- **Extensible**: Easy to add new API endpoints without changing core infrastructure
- **Centralized Authentication**: Unified token management across all endpoints
- **Consistent Monitoring**: All endpoints share the same logging and analytics

### Current Implementation
- **Certificate Processing**: Two endpoints (Standard and AI-powered)
- **User Management**: Complete authentication and authorization system
- **Processing History**: Track and export all processing activities
- **Admin Interface**: Web-based administration panel

## Configuration

### Environment Variables
Create a `.env` file in the project root:
```
SECRET_KEY=your-secret-key
DEBUG=True
DATABASE_URL=sqlite:///db.sqlite3
AZURE_OPENAI_API_KEY=your-openai-key
AZURE_OPENAI_ENDPOINT=your-openai-endpoint
```

### Adding New APIs
When you add new API endpoints:
1. Add the endpoint to `apis/urls.py`
2. Add the url to swagger_urlpatterns `SEU_Tools/seu_tools/swagger.py` 


## Security Features
- CSRF protection on all forms
- JWT token-based API authentication
- Session-based web authentication
- Rate limiting on API endpoints
- Secure file upload handling

## Deployment
- Supports Docker containerization
- Ansible playbooks for automated deployment
- Environment-specific configuration
- Static file serving via nginx

## Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License
This project is licensed under the MIT License.

## Support
For questions or issues, please contact the development team or create an issue in the repository. 