import re
from django.utils import timezone
from django.contrib.auth.models import AnonymousUser
from .models import AuditLog

# Exclude certain paths from logging (optional)
EXCLUDED_PATHS = [
    r'^/admin/jsi18n/',
    r'^/static/',
    r'^/favicon.ico',
    r'^/audit/',
]

class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Only log if user is authenticated (or we could log anonymous too)
        if hasattr(request, 'user') and request.user and not isinstance(request.user, AnonymousUser):
            path = request.path_info
            # Skip internal paths
            for pattern in EXCLUDED_PATHS:
                if re.match(pattern, path):
                    return response

            # Determine action based on path/method (simplified)
            action = self.get_action_from_request(request, response)
            if action:
                AuditLog.objects.create(
                    user=request.user,
                    username=request.user.username,
                    action=action,
                    resource=self.get_resource_from_path(path),
                    ip_address=self.get_client_ip(request),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
                )
        return response

    def get_action_from_request(self, request, response):
        method = request.method
        path = request.path_info
        if method == 'POST' and 'add' in path:
            return 'create'
        elif method == 'POST' and ('edit' in path or 'change' in path):
            return 'update'
        elif method == 'POST' and 'delete' in path:
            return 'delete'
        elif method == 'POST' and 'export' in path:
            return 'export'
        elif method == 'GET' and 'login' in path:
            return 'login'
        elif method == 'GET' and 'logout' in path:
            return 'logout'
        return None

    def get_resource_from_path(self, path):
        parts = path.strip('/').split('/')
        if len(parts) >= 1:
            return parts[0].capitalize()  # e.g., 'members' -> 'Members'
        return 'Unknown'

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip