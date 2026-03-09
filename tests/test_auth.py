"""Tests for authentication modules."""

import base64
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest
from api_client_kit.auth import BasicAuth, TokenAuth, OAuth2


class TestBasicAuth:
    """Tests for Basic Authentication."""
    
    def test_basic_auth_initialization(self):
        """Test BasicAuth can be initialized with credentials."""
        auth = BasicAuth(username="user", password="pass")
        assert auth.username == "user"
        assert auth.password == "pass"
    
    def test_basic_auth_apply(self):
        """Test BasicAuth correctly encodes credentials in Authorization header."""
        auth = BasicAuth(username="testuser", password="testpass")
        headers = {}
        
        auth.apply(headers)
        
        expected_credentials = base64.b64encode(b"testuser:testpass").decode("ascii")
        assert headers["Authorization"] == f"Basic {expected_credentials}"
    
    def test_basic_auth_apply_with_existing_headers(self):
        """Test BasicAuth merges with existing headers."""
        auth = BasicAuth(username="user", password="pass")
        headers = {"Custom-Header": "value"}
        
        auth.apply(headers)
        
        assert "Authorization" in headers
        assert headers["Custom-Header"] == "value"
    
    def test_basic_auth_special_characters(self):
        """Test BasicAuth handles special characters in credentials."""
        auth = BasicAuth(username="user@example.com", password="p@ss:word")
        headers = {}
        
        auth.apply(headers)
        
        expected_credentials = base64.b64encode(b"user@example.com:p@ss:word").decode("ascii")
        assert headers["Authorization"] == f"Basic {expected_credentials}"
    
    def test_basic_auth_is_frozen(self):
        """Test BasicAuth is immutable (frozen dataclass)."""
        auth = BasicAuth(username="user", password="pass")
        
        with pytest.raises(FrozenInstanceError):
            setattr(auth, "username", "newuser")


class TestTokenAuth:
    """Tests for Token-based Authentication."""
    
    def test_token_auth_initialization(self):
        """Test TokenAuth can be initialized with a token."""
        auth = TokenAuth(token="test-token-123")
        assert auth.token == "test-token-123"
        assert auth.scheme == "Bearer"
    
    def test_token_auth_custom_scheme(self):
        """Test TokenAuth can use custom scheme."""
        auth = TokenAuth(token="test-token", scheme="Custom")
        assert auth.scheme == "Custom"
    
    def test_token_auth_apply(self):
        """Test TokenAuth applies Bearer token to Authorization header."""
        auth = TokenAuth(token="my-token")
        headers = {}
        
        auth.apply(headers)
        
        assert headers["Authorization"] == "Bearer my-token"
    
    def test_token_auth_apply_custom_scheme(self):
        """Test TokenAuth applies custom scheme to Authorization header."""
        auth = TokenAuth(token="my-token", scheme="Token")
        headers = {}
        
        auth.apply(headers)
        
        assert headers["Authorization"] == "Token my-token"
    
    def test_token_auth_overwrites_existing_auth(self):
        """Test TokenAuth overwrites existing Authorization header."""
        auth = TokenAuth(token="new-token")
        headers = {"Authorization": "Bearer old-token"}
        
        auth.apply(headers)
        
        assert headers["Authorization"] == "Bearer new-token"
    
    def test_token_auth_is_frozen(self):
        """Test TokenAuth is immutable (frozen dataclass)."""
        auth = TokenAuth(token="test-token")
        
        with pytest.raises(FrozenInstanceError):
            setattr(auth, "token", "new-token")


class TestOAuth2:
    """Tests for OAuth 2.0 Authentication."""
    
    def test_oauth2_initialization(self):
        """Test OAuth2 can be initialized with credentials."""
        auth = OAuth2(
            client_id="client-123",
            client_secret="secret-456",
            token_url="https://auth.example.com/token"
        )
        assert auth.client_id == "client-123"
        assert auth.client_secret == "secret-456"
        assert auth.token_url == "https://auth.example.com/token"
        assert auth.access_token is None
        assert auth.scheme == "Bearer"
    
    def test_oauth2_apply_with_token(self):
        """Test OAuth2 applies Bearer token when access_token is set."""
        auth = OAuth2(
            client_id="client-123",
            client_secret="secret-456",
            token_url="https://auth.example.com/token",
            access_token="valid-token"
        )
        headers = {}
        
        auth.apply(headers)
        
        assert headers["Authorization"] == "Bearer valid-token"
    
    def test_oauth2_apply_without_token_raises_error(self):
        """Test OAuth2 raises ValueError when no access_token is set."""
        auth = OAuth2(
            client_id="client-123",
            client_secret="secret-456",
            token_url="https://auth.example.com/token"
        )
        headers = {}
        
        with pytest.raises(ValueError, match="No access token available"):
            auth.apply(headers)
    
    def test_oauth2_custom_scheme(self):
        """Test OAuth2 can use custom scheme."""
        auth = OAuth2(
            client_id="client-123",
            client_secret="secret-456",
            token_url="https://auth.example.com/token",
            access_token="token",
            scheme="DPoP"
        )
        headers = {}
        
        auth.apply(headers)
        
        assert headers["Authorization"] == "DPoP token"
    
    def test_oauth2_is_frozen(self):
        """Test OAuth2 is immutable (frozen dataclass)."""
        auth = OAuth2(
            client_id="client-123",
            client_secret="secret-456",
            token_url="https://auth.example.com/token"
        )
        
        with pytest.raises(FrozenInstanceError):
            setattr(auth, "client_id", "new-client")

    def test_oauth2_is_token_expired_without_expiry(self):
        """is_token_expired returns True when no token, False when token set but no expiry."""
        no_token = OAuth2(
            client_id="c", client_secret="s", token_url="https://x.com/token"
        )
        assert no_token.is_token_expired() is True

        with_token = OAuth2(
            client_id="c", client_secret="s", token_url="https://x.com/token",
            access_token="tok",
        )
        assert with_token.is_token_expired() is False

    def test_oauth2_is_token_expired_with_future_expiry(self):
        """is_token_expired returns False when expires_at is in the future."""
        auth = OAuth2(
            client_id="c", client_secret="s", token_url="https://x.com/token",
            access_token="tok",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        assert auth.is_token_expired() is False

    def test_oauth2_is_token_expired_with_past_expiry(self):
        """is_token_expired returns True when expires_at is in the past."""
        auth = OAuth2(
            client_id="c", client_secret="s", token_url="https://x.com/token",
            access_token="tok",
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        assert auth.is_token_expired() is True

    def test_oauth2_refresh_token(self, monkeypatch):
        """refresh_token fetches a token and updates internal state."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"access_token": "new-tok", "expires_in": 7200}
        mock_response.raise_for_status = MagicMock()

        monkeypatch.setattr("httpx.post", lambda *a, **kw: mock_response)

        auth = OAuth2(
            client_id="cid", client_secret="csec",
            token_url="https://auth.example.com/token",
        )
        token = auth.refresh_token()

        assert token == "new-tok"
        assert auth.access_token == "new-tok"
        assert auth.expires_at is not None
        assert auth.expires_at > datetime.now(timezone.utc)
