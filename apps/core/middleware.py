# ==============================================
# CORE MIDDLEWARE
# ==============================================
"""
Custom middleware for request logging, performance monitoring,
and security enhancements.
"""

import time
import logging
import json
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(MiddlewareMixin):
    """
    Middleware to log all incoming requests with timing information.
    Useful for monitoring and debugging.
    """
    
    def process_request(self, request):
        """Start timing the request."""
        request._start_time = time.time()
        
        # Log request details
        logger.debug(
            f"Request: {request.method} {request.path} "
            f"from {self.get_client_ip(request)}"
        )
    
    def process_response(self, request, response):
        """Log response time."""
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            duration_ms = int(duration * 1000)
            
            # Add timing header
            response['X-Response-Time'] = f'{duration_ms}ms'
            
            # Log slow requests
            if duration > 1.0:
                logger.warning(
                    f"Slow request: {request.method} {request.path} "
                    f"took {duration_ms}ms"
                )
            else:
                logger.debug(
                    f"Response: {request.method} {request.path} "
                    f"- {response.status_code} in {duration_ms}ms"
                )
        
        return response
    
    def get_client_ip(self, request):
        """Extract client IP from request headers."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class JSONErrorMiddleware(MiddlewareMixin):
    """
    Middleware to return JSON responses for API errors.
    Converts Django error pages to JSON for API endpoints.
    """
    
    def process_exception(self, request, exception):
        """Handle exceptions and return JSON for API requests."""
        if request.path.startswith('/api/'):
            logger.exception(f"API Error: {exception}")
            
            return JsonResponse({
                'success': False,
                'error': {
                    'message': str(exception),
                    'type': exception.__class__.__name__
                }
            }, status=500)
        
        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add additional security headers to all responses.
    """
    
    def process_response(self, request, response):
        """Add security headers."""
        # Content Security Policy
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
        )
        
        # Permissions Policy
        response['Permissions-Policy'] = (
            "geolocation=(), microphone=(), camera=()"
        )
        
        return response
