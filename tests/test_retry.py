"""Tests for retry logic."""

import pytest

from api_client_kit.retry import RetryPolicy


def test_backoff_sleep_uses_exponential_delay(monkeypatch):
    """backoff_sleep uses exponential delay when jitter is neutral."""
    sleep_calls = []

    monkeypatch.setattr("api_client_kit.retry.random.uniform", lambda _a, _b: 0.0)
    monkeypatch.setattr("api_client_kit.retry.time.sleep", lambda seconds: sleep_calls.append(seconds))

    policy = RetryPolicy(base_delay_s=0.5, max_delay_s=8.0, jitter=0.2)
    policy.backoff_sleep(3)

    assert sleep_calls == [2.0]


def test_backoff_sleep_respects_max_delay(monkeypatch):
    """backoff_sleep caps delay at max_delay_s."""
    sleep_calls = []

    monkeypatch.setattr("api_client_kit.retry.random.uniform", lambda _a, _b: 0.0)
    monkeypatch.setattr("api_client_kit.retry.time.sleep", lambda seconds: sleep_calls.append(seconds))

    policy = RetryPolicy(base_delay_s=1.0, max_delay_s=1.5, jitter=0.0)
    policy.backoff_sleep(8)

    assert sleep_calls == [pytest.approx(1.5)]
