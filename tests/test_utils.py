"""Tests for utility modules."""

from api_client_kit.utils.url import URLBuilder


def test_url_builder_base_only():
    url = URLBuilder("https://api.example.com").build()
    assert url == "https://api.example.com"


def test_url_builder_strips_trailing_slash():
    url = URLBuilder("https://api.example.com/").build()
    assert url == "https://api.example.com"


def test_url_builder_single_path():
    url = URLBuilder("https://api.example.com").add_path("v2").build()
    assert url == "https://api.example.com/v2"


def test_url_builder_multiple_paths():
    url = (
        URLBuilder("https://api.example.com")
        .add_path("v2")
        .add_path("users")
        .add_path("123")
        .build()
    )
    assert url == "https://api.example.com/v2/users/123"


def test_url_builder_query_params():
    url = (
        URLBuilder("https://api.example.com")
        .add_path("items")
        .add_query(page=1, per_page=50)
        .build()
    )
    assert "page=1" in url
    assert "per_page=50" in url
    assert url.startswith("https://api.example.com/items?")


def test_url_builder_no_query_params():
    url = URLBuilder("https://api.example.com").add_path("users").build()
    assert "?" not in url


def test_url_builder_path_strips_slashes():
    url = (
        URLBuilder("https://api.example.com")
        .add_path("/v1/")
        .add_path("/users/")
        .build()
    )
    assert url == "https://api.example.com/v1/users"


def test_url_builder_chaining_returns_self():
    builder = URLBuilder("https://x.com")
    result = builder.add_path("a").add_query(b=1)
    assert result is builder
