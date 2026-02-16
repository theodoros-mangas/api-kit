"""Pagination modules for API Client Kit."""

from .page import PagePagination
from .cursor import CursorPaginator

# Backward-compatible alias: keep older import paths working.
PagePaginator = PagePagination

__all__ = ["PagePagination", "PagePaginator", "CursorPaginator"]
