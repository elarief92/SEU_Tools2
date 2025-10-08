import json
import jwt
import logging
from datetime import datetime, timedelta
from django.shortcuts import render
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.views.generic import TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.views.generic import TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from decouple import config
from .models import User, APIToken, ProcessingHistory
from .serializers import UserSerializer, APITokenSerializer, ProcessingHistorySerializer

# Set up logging
logger = logging.getLogger('authentication')

# JWT Configuration from .env
SECRET_KEY = config("SECRET_KEY")
ALGORITHM = config("ALGORITHM", default="HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(config("ACCESS_TOKEN_EXPIRE_MINUTES", default="30"))

def create_access_token(user_id: int, username: str, expires_delta: timedelta = None):
    """Create a JWT access token."""
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {
        "user_id": user_id,
        "username": username,
        "exp": expire
    }
    
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("user_id")
        username = payload.get("username")
        if user_id is None or username is None:
            raise AuthenticationFailed("Invalid token payload")
        return {"user_id": user_id, "username": username}
    except jwt.ExpiredSignatureError:
        raise AuthenticationFailed("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthenticationFailed("Invalid token")

class JWTAuthentication(BaseAuthentication):
    """Custom JWT authentication class for DRF."""
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        try:
            payload = verify_token(token)
            user = User.objects.get(id=payload['user_id'])
            return (user, token)
        except (User.DoesNotExist, AuthenticationFailed):
            return None


class APITokenAuthentication(BaseAuthentication):
    """Custom API Token authentication class for DRF."""
    
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return None
        
        token = auth_header.split(' ')[1]
        try:
            # Try to find the token in the database
            api_token = APIToken.objects.get(token=token, is_active=True)
            
            # Check if token is expired (use timezone-aware comparison)
            from django.utils import timezone
            if api_token.expires_at and api_token.expires_at < timezone.now():
                raise AuthenticationFailed("Token has expired")
            
            # Update last used timestamp
            api_token.update_last_used()
            
            return (api_token.user, api_token)
        except APIToken.DoesNotExist:
            return None

@method_decorator(csrf_exempt, name='dispatch')
class TokenCreateView(APIView):
    """Create JWT token endpoint."""
    authentication_classes = []  # No authentication required for token creation
    permission_classes = []  # No permissions required for token creation
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        # Log authentication attempt
        client_ip = request.META.get('REMOTE_ADDR', 'unknown')
        user_agent = request.META.get('HTTP_USER_AGENT', 'unknown')
        logger.info(f"Authentication attempt for username: {username} from IP: {client_ip}")
        
        if not username or not password:
            logger.warning(f"Authentication failed - missing credentials from IP: {client_ip}")
            return Response(
                {"error": "Username and password required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = authenticate(username=username, password=password)
        if not user:
            logger.warning(f"Authentication failed - invalid credentials for username: {username} from IP: {client_ip}")
            return Response(
                {"error": "Invalid credentials"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        if not user.is_active:
            logger.warning(f"Authentication failed - disabled account for username: {username} from IP: {client_ip}")
            return Response(
                {"error": "User account is disabled"}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        # Create access token
        access_token = create_access_token(user.id, user.username)
        
        # Log successful authentication
        logger.info(f"Authentication successful for user: {username} (ID: {user.id}) from IP: {client_ip}")
        
        return Response({
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_admin": user.is_admin
            }
        })

@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    """Login view for API."""
    def post(self, request):
        # This is the same as TokenCreateView for API consistency
        token_view = TokenCreateView()
        return token_view.post(request)

class LogoutView(APIView):
    """Logout view for API."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        return Response({"message": "Successfully logged out"})

@method_decorator(csrf_exempt, name='dispatch')
class RegisterView(APIView):
    """Register view for API."""
    authentication_classes = []  # No authentication required for registration
    permission_classes = []  # No permissions required for registration
    
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not username or not password:
            return Response(
                {"error": "Username and password required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if User.objects.filter(username=username).exists():
            return Response(
                {"error": "Username already exists"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if email and User.objects.filter(email=email).exists():
            return Response(
                {"error": "Email already exists"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        
        return Response({
            "message": "User created successfully",
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email
            }
        }, status=status.HTTP_201_CREATED)

class APITokenCreateView(APIView):
    """Create API token view."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        name = request.data.get('name')
        expires_in_days = int(request.data.get('expires_in_days', 365))
        
        if not name:
            return Response(
                {"error": "Token name required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        expires_at = datetime.now() + timedelta(days=expires_in_days)
        
        api_token = APIToken.objects.create(
            user=request.user,
            name=name,
            expires_at=expires_at
        )
        
        return Response({
            "id": api_token.id,
            "token": api_token.token,
            "name": api_token.name,
            "expires_at": api_token.expires_at,
            "created_at": api_token.created_at
        }, status=status.HTTP_201_CREATED)

class APITokenRefreshView(APIView):
    """Refresh API token view."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        # Create a new JWT token for the authenticated user
        access_token = create_access_token(request.user.id, request.user.username)
        
        return Response({
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
        })

class APITokenRevokeView(APIView):
    """Revoke API token view."""
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        token_id = request.data.get('token_id')
        
        if not token_id:
            return Response(
                {"error": "Token ID required"}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            api_token = APIToken.objects.get(id=token_id, user=request.user)
            api_token.is_active = False
            api_token.save()
            
            return Response({"message": "Token revoked successfully"})
        except APIToken.DoesNotExist:
            return Response(
                {"error": "Token not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )

class UserViewSet(viewsets.ModelViewSet):
    """User management viewset."""
    queryset = User.objects.all()
    serializer_class = UserSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_admin:
            return User.objects.all()
        return User.objects.filter(id=self.request.user.id)

class APITokenViewSet(viewsets.ModelViewSet):
    """API Token management viewset."""
    queryset = APIToken.objects.all()
    serializer_class = APITokenSerializer
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        if self.request.user.is_staff or self.request.user.is_admin:
            return APIToken.objects.all()
        return APIToken.objects.filter(user=self.request.user)



class SessionLoginView(TemplateView):
    """Session-based login view for browsable API."""
    template_name = 'authentication/session_login.html'
    
    def get(self, request):
        if request.user.is_authenticated:
            return redirect('/api/')
        return render(request, self.template_name)
    
    def post(self, request):
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        if username and password:
            user = authenticate(request, username=username, password=password)
            if user:
                login(request, user)
                next_url = request.GET.get('next', '/api/')
                return redirect(next_url)
            else:
                return render(request, self.template_name, {
                    'error': 'Invalid username or password'
                })
        
        return render(request, self.template_name, {
            'error': 'Username and password are required'
        })

class SessionLogoutView(TemplateView):
    """Session-based logout view for browsable API."""
    
    def get(self, request):
        logout(request)
        return redirect('/api/auth/session-login/')
