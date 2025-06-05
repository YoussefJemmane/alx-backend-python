import logging
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    filename='requests.log',
    level=logging.INFO,
    format='%(message)s',
)

class RequestLoggingMiddleware:
    """
    Middleware that logs all requests to a file including timestamp, 
    user and request path.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get the user (authenticated or anonymous)
        user = request.user.username if request.user.is_authenticated else 'Anonymous'
        
        # Log the request with timestamp, user and path
        log_message = f"{datetime.now()} - User: {user} - Path: {request.path}"
        logger.info(log_message)
        
        # Process the request
        response = self.get_response(request)
        
        # Return the response
        return response


class RestrictAccessByTimeMiddleware:
    """
    Middleware that restricts access to the messaging app during certain hours (between 9PM and 6AM).
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Get current hour (24-hour format)
        current_hour = datetime.now().hour
        
        # Check if the current time is outside allowed hours (9PM-6AM)
        # Allowed hours: 6AM (6) to 9PM (21)
        if current_hour < 6 or current_hour >= 21:
            # Return a 403 Forbidden response if outside allowed hours
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden(
                "Access to the messaging app is not allowed between 9PM and 6AM."
            )
        
        # Process the request if within allowed hours
        response = self.get_response(request)
        return response


class OffensiveLanguageMiddleware:
    """
    Middleware that limits the number of chat messages a user can send within a certain time window (rate limiting).
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Dictionary to store message counts by IP address
        self.message_counts = {}
        # Maximum number of messages allowed per minute
        self.max_messages = 5
        # Time window in seconds (1 minute)
        self.time_window = 60

    def __call__(self, request):
        # Only apply rate limiting to POST requests to the messages endpoint
        if request.method == 'POST' and '/api/messages/' in request.path:
            # Get the client's IP address
            ip_address = self.get_client_ip(request)
            
            # Get the current timestamp
            current_time = datetime.now()
            
            # Initialize or clean up the message counts for this IP
            if ip_address not in self.message_counts:
                self.message_counts[ip_address] = []
            
            # Remove timestamps older than the time window
            self.message_counts[ip_address] = [timestamp for timestamp in self.message_counts[ip_address] 
                                              if (current_time - timestamp).total_seconds() < self.time_window]
            
            # Check if the user has exceeded the rate limit
            if len(self.message_counts[ip_address]) >= self.max_messages:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden(
                    f"Rate limit exceeded. Please wait before sending more messages. Maximum {self.max_messages} messages per {self.time_window} seconds."
                )
            
            # Add the current timestamp to the list
            self.message_counts[ip_address].append(current_time)
        
        # Process the request
        response = self.get_response(request)
        
        return response
    
    def get_client_ip(self, request):
        """
        Get the client's IP address from the request
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class RolePermissionMiddleware:
    """
    Middleware that checks the user's role before allowing access to admin-only actions.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Admin-only endpoints
        self.admin_endpoints = [
            '/api/admin/',
            '/api/users/manage/',
            '/api/conversations/delete/',
            '/api/conversations/moderate/',
        ]

    def __call__(self, request):
        # Check if the endpoint requires admin privileges
        requires_admin = any(endpoint in request.path for endpoint in self.admin_endpoints)
        
        if requires_admin:
            # Check if user is authenticated
            if not request.user.is_authenticated:
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Authentication required for this action.")
            
            # Check if user is admin or moderator
            if not (request.user.is_staff or request.user.is_superuser):
                from django.http import HttpResponseForbidden
                return HttpResponseForbidden("Admin or moderator privileges required for this action.")
        
        # Process the request if user has appropriate permissions
        response = self.get_response(request)
        return response
