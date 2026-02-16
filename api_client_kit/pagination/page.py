from __future__ import annotations
from dataclasses import dataclass
from typing import Callable, Iterator, Any

Json = dict[str, Any]

@dataclass(frozen=True)
class PagePagination:
    """Page-based: ?page=1&per_page=50"""
    start_page: int = 1
    page_param: str = "page"
    per_page_param: str = "per_page"
    per_page: int = 50
    items_path: str = "data"   # where items list lives in JSON
    next_page_path: str | None = None  # optional if API returns next page value

    def iterate(
        self,
        fetch_json: Callable[[dict[str, Any]], Json],
        params: dict[str, Any] | None = None,
        max_pages: int | None = None,
    ) -> Iterator[dict]:
        p = dict(params or {})
        page = self.start_page
        pages_seen = 0

        while True:
            p[self.page_param] = page
            p[self.per_page_param] = self.per_page
            data = fetch_json(p)

            items = data.get(self.items_path, [])
            if not isinstance(items, list):
                raise ValueError(f"Expected list at '{self.items_path}'")

            for it in items:
                yield it

            pages_seen += 1
            if max_pages and pages_seen >= max_pages:
                return

            if self.next_page_path:
                nxt = data.get(self.next_page_path)
                if not nxt:
                    return
                page = int(nxt)
            else:
                if not items:  # common stop condition
                    return
                page += 1
