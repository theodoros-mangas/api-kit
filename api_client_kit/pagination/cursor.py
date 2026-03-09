"""Cursor-based pagination implementation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterator

Json = dict[str, Any]


@dataclass(frozen=True)
class CursorPaginator:
    """Cursor-based pagination: follows a cursor/next token through pages.

    Many APIs return a ``next_cursor`` (or similar) field that must be
    passed back as a query parameter to fetch the next page.
    """

    cursor_param: str = "cursor"
    items_path: str = "data"
    next_cursor_path: str = "next_cursor"
    per_page: int = 50
    per_page_param: str = "per_page"

    def iterate(
        self,
        fetch_json: Callable[[dict[str, Any]], Json],
        params: dict[str, Any] | None = None,
        max_pages: int | None = None,
    ) -> Iterator[dict[str, Any]]:
        """Yield items across all pages until the cursor is exhausted."""
        p = dict(params or {})
        p[self.per_page_param] = self.per_page
        pages_seen = 0

        while True:
            data = fetch_json(p)

            items = data.get(self.items_path, [])
            if not isinstance(items, list):
                raise ValueError(f"Expected list at '{self.items_path}'")

            yield from items

            pages_seen += 1
            if max_pages and pages_seen >= max_pages:
                return

            next_cursor = data.get(self.next_cursor_path)
            if not next_cursor:
                return
            p[self.cursor_param] = next_cursor
