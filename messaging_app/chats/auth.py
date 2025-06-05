from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from django.conf import settings

class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT Authentication class for additional functionality
    """
    def authenticate(self, request):
        """
        Attempt to authenticate the request using JWT.
        """
        try:
            return super().authenticate(request)
        except InvalidToken:
            return None

def get_tokens_for_user(user):
    """
    Generate JWT tokens for a user
    """
    refresh = RefreshToken.for_user(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }

