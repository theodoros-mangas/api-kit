"""Tests for configuration module."""

import os

import pytest

from api_client_kit.config import Config


def test_config_defaults():
    cfg = Config()
    assert cfg.base_url == ""
    assert cfg.timeout_s == 15.0
    assert cfg.max_retries == 3
    assert cfg.default_headers == {}


def test_config_custom_values():
    cfg = Config(
        base_url="https://api.example.com",
        timeout_s=30.0,
        max_retries=5,
        default_headers={"X-App": "test"},
    )
    assert cfg.base_url == "https://api.example.com"
    assert cfg.timeout_s == 30.0
    assert cfg.max_retries == 5
    assert cfg.default_headers == {"X-App": "test"}


def test_config_from_env(monkeypatch):
    monkeypatch.setenv("API_BASE_URL", "https://env.example.com")
    monkeypatch.setenv("API_TIMEOUT", "25.5")
    monkeypatch.setenv("API_MAX_RETRIES", "7")

    cfg = Config.from_env()

    assert cfg.base_url == "https://env.example.com"
    assert cfg.timeout_s == 25.5
    assert cfg.max_retries == 7


def test_config_from_env_defaults(monkeypatch):
    monkeypatch.delenv("API_BASE_URL", raising=False)
    monkeypatch.delenv("API_TIMEOUT", raising=False)
    monkeypatch.delenv("API_MAX_RETRIES", raising=False)

    cfg = Config.from_env()

    assert cfg.base_url == ""
    assert cfg.timeout_s == 15.0
    assert cfg.max_retries == 3


def test_config_is_frozen():
    cfg = Config(base_url="https://x.com")
    with pytest.raises(AttributeError):
        cfg.base_url = "https://other.com" #type: ignore
