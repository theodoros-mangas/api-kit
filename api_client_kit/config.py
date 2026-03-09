"""Configuration management for API clients."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Config:
    """Immutable configuration container for an API client.

    Values can be supplied directly or pulled from environment variables
    via :meth:`from_env`.
    """

    base_url: str = ""
    timeout_s: float = 15.0
    max_retries: int = 3
    default_headers: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_env(
        cls,
        *,
        url_var: str = "API_BASE_URL",
        timeout_var: str = "API_TIMEOUT",
        retries_var: str = "API_MAX_RETRIES",
    ) -> Config:
        """Create a :class:`Config` from environment variables."""
        return cls(
            base_url=os.environ.get(url_var, ""),
            timeout_s=float(os.environ.get(timeout_var, "15.0")),
            max_retries=int(os.environ.get(retries_var, "3")),
        )
