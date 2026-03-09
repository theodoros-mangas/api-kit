"""Unit tests for the API client."""

import httpx
import pytest

from api_client_kit.auth import TokenAuth
from api_client_kit.client import APIClient
from api_client_kit.errors import APIError, Forbidden, NotFound, RateLimited, Unauthorized
from api_client_kit.retry import RetryPolicy


def _response(status_code: int, *, json_body=None, text: str = "", headers=None) -> httpx.Response:
    req = httpx.Request("GET", "https://example.com/resource")
    if json_body is not None:
        return httpx.Response(status_code, json=json_body, request=req, headers=headers or {})
    return httpx.Response(status_code, text=text, request=req, headers=headers or {})


# ---------------------------------------------------------------------------
# Header building
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Status-code mapping
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# _request retry loop
# ---------------------------------------------------------------------------

def test_request_retries_on_server_error(monkeypatch):
    """_request retries on 5xx and eventually returns on success."""
    monkeypatch.setattr("api_client_kit.retry.time.sleep", lambda _: None)
    monkeypatch.setattr("api_client_kit.retry.random.uniform", lambda _a, _b: 0.0)

    call_count = 0

    def mock_request(self, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return _response(500, json_body={"error": "internal"})
        return _response(200, json_body={"ok": True})

    monkeypatch.setattr(httpx.Client, "request", mock_request)

    client = APIClient(base_url="https://api.example.com", retry=RetryPolicy(max_attempts=3))
    resp = client._request("GET", "/test")
    assert resp.status_code == 200
    assert call_count == 3


def test_request_raises_after_max_retries_on_server_error(monkeypatch):
    """_request raises APIError after exhausting retries on 5xx."""
    monkeypatch.setattr("api_client_kit.retry.time.sleep", lambda _: None)
    monkeypatch.setattr("api_client_kit.retry.random.uniform", lambda _a, _b: 0.0)

    def mock_request(self, **kwargs):
        return _response(503, json_body={"error": "unavailable"})

    monkeypatch.setattr(httpx.Client, "request", mock_request)

    client = APIClient(base_url="https://api.example.com", retry=RetryPolicy(max_attempts=2))
    with pytest.raises(APIError) as exc_info:
        client._request("GET", "/fail")
    assert exc_info.value.status_code == 503


def test_request_retries_on_timeout(monkeypatch):
    """_request retries on httpx.TimeoutException."""
    monkeypatch.setattr("api_client_kit.retry.time.sleep", lambda _: None)
    monkeypatch.setattr("api_client_kit.retry.random.uniform", lambda _a, _b: 0.0)

    call_count = 0

    def mock_request(self, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise httpx.ReadTimeout("timed out")
        return _response(200, json_body={"ok": True})

    monkeypatch.setattr(httpx.Client, "request", mock_request)

    client = APIClient(base_url="https://api.example.com", retry=RetryPolicy(max_attempts=3))
    resp = client._request("GET", "/slow")
    assert resp.status_code == 200
    assert call_count == 2


def test_request_handles_rate_limit_with_retry_after(monkeypatch):
    """_request respects Retry-After header on 429."""
    sleep_durations: list[float] = []
    monkeypatch.setattr("api_client_kit.retry.time.sleep", lambda _: None)
    monkeypatch.setattr("api_client_kit.retry.random.uniform", lambda _a, _b: 0.0)
    # Capture the time.sleep calls from the rate-limit path
    import api_client_kit.client as client_mod
    import time as time_mod
    original_sleep = time_mod.sleep
    monkeypatch.setattr(time_mod, "sleep", lambda s: sleep_durations.append(s))

    call_count = 0

    def mock_request(self, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _response(429, json_body={"error": "rate limited"}, headers={"Retry-After": "2"})
        return _response(200, json_body={"ok": True})

    monkeypatch.setattr(httpx.Client, "request", mock_request)

    client = APIClient(base_url="https://api.example.com", retry=RetryPolicy(max_attempts=3))
    resp = client._request("GET", "/limited")
    assert resp.status_code == 200
    assert 2.0 in sleep_durations


# ---------------------------------------------------------------------------
# Public helper methods
# ---------------------------------------------------------------------------

def test_get_json(monkeypatch):
    """get_json returns parsed JSON on 200."""
    def mock_request(self, **kwargs):
        return _response(200, json_body={"id": 1, "name": "test"})

    monkeypatch.setattr(httpx.Client, "request", mock_request)

    client = APIClient(base_url="https://api.example.com")
    result = client.get_json("/resource")
    assert result == {"id": 1, "name": "test"}


def test_post_json(monkeypatch):
    """post_json sends JSON body and returns parsed response."""
    def mock_request(self, **kwargs):
        return _response(201, json_body={"id": 42})

    monkeypatch.setattr(httpx.Client, "request", mock_request)

    client = APIClient(base_url="https://api.example.com")
    result = client.post_json("/resource", json_body={"name": "new"})
    assert result == {"id": 42}


def test_put_json(monkeypatch):
    """put_json sends JSON body and returns parsed response."""
    def mock_request(self, **kwargs):
        return _response(200, json_body={"id": 1, "updated": True})

    monkeypatch.setattr(httpx.Client, "request", mock_request)

    client = APIClient(base_url="https://api.example.com")
    result = client.put_json("/resource/1", json_body={"name": "updated"})
    assert result == {"id": 1, "updated": True}


def test_patch_json(monkeypatch):
    """patch_json sends partial update and returns parsed response."""
    def mock_request(self, **kwargs):
        return _response(200, json_body={"id": 1, "name": "patched"})

    monkeypatch.setattr(httpx.Client, "request", mock_request)

    client = APIClient(base_url="https://api.example.com")
    result = client.patch_json("/resource/1", json_body={"name": "patched"})
    assert result == {"id": 1, "name": "patched"}


def test_delete(monkeypatch):
    """delete sends DELETE and does not raise on 204."""
    def mock_request(self, **kwargs):
        return _response(204)

    monkeypatch.setattr(httpx.Client, "request", mock_request)

    client = APIClient(base_url="https://api.example.com")
    # Should not raise
    client.delete("/resource/1")
