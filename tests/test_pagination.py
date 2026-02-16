"""Tests for pagination modules."""

import pytest

from api_client_kit.pagination import PagePagination


def test_page_pagination_iterates_until_empty_page():
    """PagePagination stops when an empty page is returned."""
    responses = [
        {"data": [{"id": 1}, {"id": 2}]},
        {"data": [{"id": 3}]},
        {"data": []},
    ]
    params_seen = []

    def fetch_json(params):
        params_seen.append(dict(params))
        return responses.pop(0)

    paginator = PagePagination(per_page=2)
    items = list(paginator.iterate(fetch_json))

    assert items == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert params_seen == [
        {"page": 1, "per_page": 2},
        {"page": 2, "per_page": 2},
        {"page": 3, "per_page": 2},
    ]


def test_page_pagination_raises_for_non_list_items():
    """PagePagination validates that the configured items path is a list."""
    paginator = PagePagination()

    def fetch_json(_params):
        return {"data": {"id": 1}}

    with pytest.raises(ValueError, match="Expected list"):
        list(paginator.iterate(fetch_json))


def test_page_pagination_with_next_page_path():
    """PagePagination follows the provided next-page field."""
    responses = [
        {"data": [{"id": 1}], "next_page": 2},
        {"data": [{"id": 2}], "next_page": None},
    ]
    params_seen = []

    def fetch_json(params):
        params_seen.append(dict(params))
        return responses.pop(0)

    paginator = PagePagination(next_page_path="next_page", per_page=1)
    items = list(paginator.iterate(fetch_json))

    assert items == [{"id": 1}, {"id": 2}]
    assert params_seen == [
        {"page": 1, "per_page": 1},
        {"page": 2, "per_page": 1},
    ]
