"""Unit tests for the API client."""

import httpx
import pytest

from api_client_kit.auth import TokenAuth
from api_client_kit.client import APIClient
from api_client_kit.errors import APIError, Forbidden, NotFound, Unauthorized


def _response(status_code: int, *, json_body=None, text: str = "") -> httpx.Response:
    req = httpx.Request("GET", "https://example.com/resource")
    if json_body is not None:
        return httpx.Response(status_code, json=json_body, request=req)
    return httpx.Response(status_code, text=text, request=req)


def test_build_headers_merges_defaults_extra_and_auth():
    client = APIClient(
        base_url="https://api.example.com",
        default_headers={"X-App": "kit"},
        auth=TokenAuth("token-123"),
    )

    headers = client._build_headers({"X-Trace": "abc"})

    assert headers["Accept"] == "application/json"
    assert headers["X-App"] == "kit"
    assert headers["X-Trace"] == "abc"
    assert headers["Authorization"] == "Bearer token-123"


def test_raise_for_status_maps_known_errors():
    client = APIClient(base_url="https://api.example.com")

    with pytest.raises(Unauthorized):
        client._raise_for_status(_response(401, json_body={"message": "nope"}))

    with pytest.raises(Forbidden):
        client._raise_for_status(_response(403, json_body={"message": "forbidden"}))

    with pytest.raises(NotFound):
        client._raise_for_status(_response(404, json_body={"message": "missing"}))


def test_raise_for_status_uses_generic_api_error_for_other_4xx_5xx():
    client = APIClient(base_url="https://api.example.com")

    with pytest.raises(APIError) as exc_info:
        client._raise_for_status(_response(418, text="teapot"))

    assert exc_info.value.status_code == 418


def test_safe_json_returns_none_for_non_json_response():
    client = APIClient(base_url="https://api.example.com")
    response = _response(200, text="plain-text")

    assert client._safe_json(response) is None
