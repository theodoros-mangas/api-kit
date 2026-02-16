"""Token-based authentication implementation."""

from .base import AuthHandler


class TokenAuth(AuthHandler):
    """Token-based authentication handler."""
    
    def __init__(self, token: str, token_type: str = "Bearer"):
        """Initialize TokenAuth with a token.
        
        Args:
            token: The authentication token.
            token_type: The type of token (default: Bearer).
        """
        self.token = token
        self.token_type = token_type
    
    def apply(self, request):
        """Apply token authentication to a request."""
        pass
