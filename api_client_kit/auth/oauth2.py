"""OAuth 2.0 authentication implementation."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import httpx

from .base import AuthStrategy

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class OAuth2(AuthStrategy):
    """OAuth 2.0 authentication handler with token expiry tracking.

    Supports the *client-credentials* grant type.  Call
    :meth:`refresh_token` (or :meth:`async_refresh_token`) to obtain a
    new access token; the result is stored on the (frozen) instance via
    ``object.__setattr__``.
    """

    client_id: str
    client_secret: str
    token_url: str
    access_token: Optional[str] = None
    scheme: str = "Bearer"
    expires_at: Optional[datetime] = None
    _token_data: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)

    # --- AuthStrategy interface ------------------------------------------

    def apply(self, headers: dict[str, str]) -> None:
        """Apply the current access token to *headers*.

        Raises:
            ValueError: If no access token has been set yet.
        """
        if self.access_token:
            headers["Authorization"] = f"{self.scheme} {self.access_token}"
        else:
            raise ValueError("No access token available. Call refresh_token() first.")

    # --- token helpers ---------------------------------------------------

    def is_token_expired(self) -> bool:
        """Return ``True`` when the token is missing or past its expiry."""
        if self.expires_at is None:
            return self.access_token is None
        return datetime.now(timezone.utc) >= self.expires_at

    def refresh_token(self) -> str:
        """Fetch a new token via the *client_credentials* grant.

        Updates ``access_token``, ``expires_at`` and ``_token_data`` on
        this (frozen) instance and returns the new token string.
        """
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        try:
            response = httpx.post(self.token_url, data=data)
            response.raise_for_status()
            token_data: Dict[str, Any] = response.json()
        except Exception as exc:
            logger.error("OAuth2: Failed to refresh token: %s", exc)
            raise

        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

        object.__setattr__(self, "access_token", access_token)
        object.__setattr__(self, "expires_at", expires_at)
        object.__setattr__(self, "_token_data", token_data)
        logger.info("OAuth2: Refreshed token, expires at %s.", expires_at)
        return access_token  # type: ignore[return-value]

    async def async_refresh_token(self) -> str:
        """Async variant of :meth:`refresh_token`."""
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(self.token_url, data=data)
                response.raise_for_status()
                token_data: Dict[str, Any] = response.json()
        except Exception as exc:
            logger.error("OAuth2: Failed to refresh token (async): %s", exc)
            raise

        access_token = token_data.get("access_token")
        expires_in = token_data.get("expires_in", 3600)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=int(expires_in))

        object.__setattr__(self, "access_token", access_token)
        object.__setattr__(self, "expires_at", expires_at)
        object.__setattr__(self, "_token_data", token_data)
        logger.info("OAuth2: Refreshed token (async), expires at %s.", expires_at)
        return access_token  # type: ignore[return-value]
