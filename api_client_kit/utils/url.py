"""URL building and manipulation utilities."""

from __future__ import annotations

from urllib.parse import urlencode, urljoin, urlparse, urlunparse


class URLBuilder:
    """Fluent helper for constructing URLs with path segments and query params.

    Example::

        url = (
            URLBuilder("https://api.example.com")
            .add_path("v2")
            .add_path("users")
            .add_query(page=1, per_page=50)
            .build()
        )
        # -> "https://api.example.com/v2/users?page=1&per_page=50"
    """

    def __init__(self, base_url: str) -> None:
        self._base = base_url.rstrip("/")
        self._segments: list[str] = []
        self._params: dict[str, str] = {}

    def add_path(self, segment: str) -> URLBuilder:
        """Append a path segment (leading/trailing slashes are stripped)."""
        self._segments.append(segment.strip("/"))
        return self

    def add_query(self, **kwargs: object) -> URLBuilder:
        """Add query parameters (values are converted to strings)."""
        for key, value in kwargs.items():
            self._params[key] = str(value)
        return self

    def build(self) -> str:
        """Return the fully-constructed URL string."""
        path = "/".join([self._base] + self._segments)
        if self._params:
            return f"{path}?{urlencode(self._params)}"
        return path

    def __str__(self) -> str:  # pragma: no cover
        return self.build()
