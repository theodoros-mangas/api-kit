"""Tests for pagination modules."""

import pytest

from api_client_kit.pagination import PagePagination, CursorPaginator


# ---------------------------------------------------------------------------
# PagePagination
# ---------------------------------------------------------------------------

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


def test_page_pagination_respects_max_pages():
    """PagePagination stops after max_pages even if data remains."""
    responses = [
        {"data": [{"id": 1}]},
        {"data": [{"id": 2}]},
        {"data": [{"id": 3}]},
    ]

    def fetch_json(_params):
        return responses.pop(0)

    paginator = PagePagination(per_page=1)
    items = list(paginator.iterate(fetch_json, max_pages=2))

    assert items == [{"id": 1}, {"id": 2}]


# ---------------------------------------------------------------------------
# CursorPaginator
# ---------------------------------------------------------------------------

def test_cursor_paginator_follows_cursor():
    """CursorPaginator follows next_cursor until exhausted."""
    responses = [
        {"data": [{"id": 1}], "next_cursor": "abc"},
        {"data": [{"id": 2}], "next_cursor": "def"},
        {"data": [{"id": 3}], "next_cursor": None},
    ]
    params_seen = []

    def fetch_json(params):
        params_seen.append(dict(params))
        return responses.pop(0)

    paginator = CursorPaginator(per_page=1)
    items = list(paginator.iterate(fetch_json))

    assert items == [{"id": 1}, {"id": 2}, {"id": 3}]
    assert params_seen[0] == {"per_page": 1}
    assert params_seen[1]["cursor"] == "abc"
    assert params_seen[2]["cursor"] == "def"


def test_cursor_paginator_stops_on_empty_data():
    """CursorPaginator stops when items list is empty and no cursor."""
    responses = [
        {"data": [], "next_cursor": None},
    ]

    def fetch_json(_params):
        return responses.pop(0)

    paginator = CursorPaginator()
    items = list(paginator.iterate(fetch_json))
    assert items == []


def test_cursor_paginator_raises_for_non_list():
    """CursorPaginator validates items_path is a list."""
    def fetch_json(_params):
        return {"data": "not-a-list", "next_cursor": None}

    paginator = CursorPaginator()
    with pytest.raises(ValueError, match="Expected list"):
        list(paginator.iterate(fetch_json))


def test_cursor_paginator_respects_max_pages():
    """CursorPaginator stops after max_pages."""
    responses = [
        {"data": [{"id": 1}], "next_cursor": "abc"},
        {"data": [{"id": 2}], "next_cursor": "def"},
        {"data": [{"id": 3}], "next_cursor": None},
    ]

    def fetch_json(_params):
        return responses.pop(0)

    paginator = CursorPaginator(per_page=1)
    items = list(paginator.iterate(fetch_json, max_pages=2))
    assert items == [{"id": 1}, {"id": 2}]


def test_cursor_paginator_custom_field_names():
    """CursorPaginator works with custom parameter/field names."""
    responses = [
        {"results": [{"id": 1}], "continuation": "tok1"},
        {"results": [{"id": 2}], "continuation": None},
    ]

    def fetch_json(params):
        return responses.pop(0)

    paginator = CursorPaginator(
        cursor_param="continuation_token",
        items_path="results",
        next_cursor_path="continuation",
    )
    items = list(paginator.iterate(fetch_json))
    assert items == [{"id": 1}, {"id": 2}]
