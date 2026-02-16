"""Basic authentication implementation."""

from .base import AuthHandler


class BasicAuth(AuthHandler):
    """HTTP Basic Authentication handler."""
    
    def __init__(self, username: str, password: str):
        """Initialize BasicAuth with credentials.
        
        Args:
            username: The username for authentication.
            password: The password for authentication.
        """
        self.username = username
        self.password = password
    
    def apply(self, request):
        """Apply basic authentication to a request."""
        pass
