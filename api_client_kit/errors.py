"""Custom exceptions for API client kit."""


class APIKitError(Exception):
    """Base exception for API Client Kit."""
    
    pass


class APIError(APIKitError):
    """Exception raised for API errors."""
    
    pass


class AuthenticationError(APIKitError):
    """Exception raised for authentication failures."""
    
    pass


class ConfigurationError(APIKitError):
    """Exception raised for configuration issues."""
    
    pass
