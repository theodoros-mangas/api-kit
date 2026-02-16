"""Base authentication handler."""

from abc import ABC, abstractmethod


class AuthHandler(ABC):
    """Base class for authentication handlers."""
    
    @abstractmethod
    def apply(self, request):
        """Apply authentication to a request."""
        pass
