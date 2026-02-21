import json
from django.utils.deprecation import MiddlewareMixin
from .models import AuditLog

class AuditLogMiddleware(MiddlewareMixin):
    """
    Middleware to log all requests for auditing
    """
    
    def process_request(self, request):
        request._audit_data = {
            'ip_address': self.get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
        }
    
    def process_response(self, request, response):
        # Only log API requests
        if request.path.startswith('/api/') and request.user.is_authenticated:
            if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                # Don't log sensitive endpoints
                sensitive_paths = ['/api/auth/login/', '/api/auth/biometric-login/']
                if not any(path in request.path for path in sensitive_paths):
                    self.create_audit_log(request, response)
        return response
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def create_audit_log(self, request, response):
        try:
            # Try to parse request body
            body = json.loads(request.body) if request.body else {}
        except:
            body = {}
        
        # Try to parse response content
        try:
            if hasattr(response, 'content') and response.content:
                response_data = json.loads(response.content)
            else:
                response_data = {}
        except:
            response_data = {}
        
        AuditLog.objects.create(
            user_id=request.user.id,
            action=request.method.lower(),
            resource_type=request.path.split('/')[-2] if len(request.path.split('/')) > 2 else 'unknown',
            description=f"{request.method} {request.path}",
            ip_address=request._audit_data['ip_address'],
            user_agent=request._audit_data['user_agent'],
            new_values=body if request.method in ['POST', 'PUT'] else {},
            old_values={}  # Would need to fetch previous state for updates
        )