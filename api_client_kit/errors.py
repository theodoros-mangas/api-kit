"""Custom exceptions for API client kit."""

from typing import Any, Optional


class APIKitError(Exception):
    """Base exception for API Client Kit."""
    pass


class APIError(APIKitError):
    """Exception raised for API errors."""
    
    def __init__(self, status_code: int, message: str, payload: Any = None):
        self.status_code = status_code
        self.message = message
        self.payload = payload
        super().__init__(f"{status_code}: {message}")


class AuthenticationError(APIKitError):
    """Exception raised for authentication failures."""
    pass


class ConfigurationError(APIKitError):
    """Exception raised for configuration issues."""
    pass


class Unauthorized(APIError):
    """Exception raised for 401 Unauthorized responses."""
    pass


class Forbidden(APIError):
    """Exception raised for 403 Forbidden responses."""
    pass


class NotFound(APIError):
    """Exception raised for 404 Not Found responses."""
    pass


class RateLimited(APIError):
    """Exception raised when rate limited (429)."""
    
    def __init__(self, status_code: int, message: str, retry_after: Optional[float] = None, payload: Any = None):
        super().__init__(status_code, message, payload)
        self.retry_after = retry_after
