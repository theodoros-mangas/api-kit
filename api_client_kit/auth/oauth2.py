"""OAuth 2.0 authentication implementation."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional
import httpx
from .base import AuthStrategy


@dataclass(frozen=True)
class OAuth2(AuthStrategy):
    """OAuth 2.0 authentication handler."""
    
    client_id: str
    client_secret: str
    token_url: str
    access_token: Optional[str] = None
    scheme: str = "Bearer"

    def apply(self, headers: dict[str, str]) -> None:
        """Apply OAuth 2.0 authentication to a request.
        
        Args:
            headers: The request headers dict to mutate in-place.
        """
        if self.access_token:
            headers["Authorization"] = f"{self.scheme} {self.access_token}"
        else:
            raise ValueError("No access token available. Call refresh_token() first.")

    def refresh_token(self) -> str:
        """Refresh the OAuth 2.0 access token.
        
        Returns:
            The new access token.
            
        Raises:
            Exception: If token refresh fails.
        """
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        
        response = httpx.post(self.token_url, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        return token_data.get("access_token")
