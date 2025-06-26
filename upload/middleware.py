"""
Custom middleware to ensure proper HTTPS detection in Azure Container Apps/App Service.
This middleware forces Django to recognize HTTPS when running behind Azure's load balancer.
"""

from django.utils import timezone
from django.http import JsonResponse
from .models import UserSession
import logging

logger = logging.getLogger(__name__)

class ForceHttpsMiddleware:
    """
    Middleware to force HTTPS detection when running behind Azure load balancer.
    
    Azure Container Apps and App Service terminate SSL at the load balancer,
    so Django doesn't automatically detect HTTPS. This middleware ensures
    that request.is_secure() returns True in production environments.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Check if we should force HTTPS detection
        from django.conf import settings
        
        # Force HTTPS detection in production or when explicitly enabled
        force_https = (
            not getattr(settings, 'DEBUG', True) or 
            getattr(settings, 'FORCE_HTTPS_DETECTION', False)
        )
        
        if force_https:
            # Check for Azure-specific headers that indicate HTTPS
            x_forwarded_proto = request.META.get('HTTP_X_FORWARDED_PROTO', '')
            x_arr_ssl = request.META.get('HTTP_X_ARR_SSL', '')  # Azure App Service specific
            
            # Force secure if:
            # 1. X-Forwarded-Proto is https (standard proxy header)
            # 2. X-ARR-SSL is present (Azure App Service specific)
            # 3. We're in production mode (assume HTTPS)
            if (x_forwarded_proto.lower() == 'https' or 
                x_arr_ssl or 
                not getattr(settings, 'DEBUG', True)):
                
                # Override the request to force secure detection
                request.META['wsgi.url_scheme'] = 'https'
                # Also set HTTPS environment for the request
                request.META['HTTPS'] = 'on'
        
        response = self.get_response(request)
        return response

class UserSessionMiddleware:
    """
    Middleware to handle user session management for file isolation.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process request before view
        self.process_request(request)
        
        response = self.get_response(request)
        return response

    def process_request(self, request):
        """
        Add user session info to request if available.
        """
        session_key = request.session.session_key
        if session_key:
            try:
                user_session = UserSession.objects.get(session_key=session_key)
                # Update last activity
                user_session.last_activity = timezone.now()
                user_session.save()
                
                # Add user info to request
                request.user_email = user_session.user_email
                request.user_id_hash = user_session.user_id_hash
                request.user_session = user_session
                
            except UserSession.DoesNotExist:
                # No user session found
                request.user_email = None
                request.user_id_hash = None
                request.user_session = None
        else:
            request.user_email = None
            request.user_id_hash = None
            request.user_session = None

def require_user_session(view_func):
    """
    Decorator to require a valid user session for a view.
    """
    def wrapper(request, *args, **kwargs):
        if not hasattr(request, 'user_session') or not request.user_session:
            return JsonResponse({'error': 'User session required. Please upload a file first.'}, status=401)
        return view_func(request, *args, **kwargs)
    return wrapper
