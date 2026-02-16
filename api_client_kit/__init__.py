"""API Client Kit - A comprehensive toolkit for building API clients."""

from .client import APIClient
from .auth import OAuth2, BasicAuth, TokenAuth
from .errors import APIError, AuthenticationError, ConfigurationError, RateLimited

__version__ = "0.1.0"

__all__ = [
    "APIClient",
    "OAuth2",
    "BasicAuth",
    "TokenAuth",
    "APIError",
    "AuthenticationError",
    "ConfigurationError",
    "RateLimited",
]
