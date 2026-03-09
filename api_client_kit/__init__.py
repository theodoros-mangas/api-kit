"""API Client Kit - A comprehensive toolkit for building API clients."""

from .client import APIClient
from .auth import OAuth2, BasicAuth, TokenAuth
from .errors import APIError, AuthenticationError, ConfigurationError, RateLimited
from .retry import RetryPolicy

__version__ = "0.1.0"

__all__ = [
    "APIClient",
    "OAuth2",
    "BasicAuth",
    "TokenAuth",
    "RetryPolicy",
    "APIError",
    "AuthenticationError",
    "ConfigurationError",
    "RateLimited",
]
