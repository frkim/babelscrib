"""
Custom middleware to ensure proper HTTPS detection in Azure Container Apps/App Service.
This middleware forces Django to recognize HTTPS when running behind Azure's load balancer.
"""

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
