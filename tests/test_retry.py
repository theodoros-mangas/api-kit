"""Tests for retry logic."""

import asyncio

import pytest

from api_client_kit.retry import RetryPolicy


# ---------------------------------------------------------------------------
# backoff_sleep
# ---------------------------------------------------------------------------

def test_backoff_sleep_uses_exponential_delay(monkeypatch):
    """backoff_sleep uses exponential delay when jitter is neutral."""
    sleep_calls: list[float] = []

    monkeypatch.setattr("api_client_kit.retry.random.uniform", lambda _a, _b: 0.0)
    monkeypatch.setattr("api_client_kit.retry.time.sleep", lambda seconds: sleep_calls.append(seconds))

    policy = RetryPolicy(base_delay_s=0.5, max_delay_s=8.0, jitter=0.2)
    policy.backoff_sleep(3)

    assert sleep_calls == [2.0]


def test_backoff_sleep_respects_max_delay(monkeypatch):
    """backoff_sleep caps delay at max_delay_s."""
    sleep_calls: list[float] = []

    monkeypatch.setattr("api_client_kit.retry.random.uniform", lambda _a, _b: 0.0)
    monkeypatch.setattr("api_client_kit.retry.time.sleep", lambda seconds: sleep_calls.append(seconds))

    policy = RetryPolicy(base_delay_s=1.0, max_delay_s=1.5, jitter=0.0)
    policy.backoff_sleep(8)

    assert sleep_calls == [pytest.approx(1.5)]


# ---------------------------------------------------------------------------
# retry decorator (sync)
# ---------------------------------------------------------------------------

def test_retry_decorator_succeeds_on_first_attempt(monkeypatch):
    """Decorated function that succeeds immediately is called once."""
    monkeypatch.setattr("api_client_kit.retry.time.sleep", lambda _: None)

    policy = RetryPolicy(max_attempts=3)
    call_count = 0

    @policy.retry
    def succeed():
        nonlocal call_count
        call_count += 1
        return "ok"

    assert succeed() == "ok"
    assert call_count == 1


def test_retry_decorator_retries_on_failure(monkeypatch):
    """Decorated function is retried up to max_attempts."""
    monkeypatch.setattr("api_client_kit.retry.time.sleep", lambda _: None)
    monkeypatch.setattr("api_client_kit.retry.random.uniform", lambda _a, _b: 0.0)

    policy = RetryPolicy(max_attempts=3)
    call_count = 0

    @policy.retry
    def fail_twice():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("transient")
        return "recovered"

    assert fail_twice() == "recovered"
    assert call_count == 3


def test_retry_decorator_raises_after_max_attempts(monkeypatch):
    """After exhausting attempts the last exception is raised."""
    monkeypatch.setattr("api_client_kit.retry.time.sleep", lambda _: None)
    monkeypatch.setattr("api_client_kit.retry.random.uniform", lambda _a, _b: 0.0)

    policy = RetryPolicy(max_attempts=2)

    @policy.retry
    def always_fail():
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError, match="boom"):
        always_fail()


def test_retry_decorator_with_on_kwarg(monkeypatch):
    """The `on=` parameter restricts which exceptions trigger retries."""
    monkeypatch.setattr("api_client_kit.retry.time.sleep", lambda _: None)
    monkeypatch.setattr("api_client_kit.retry.random.uniform", lambda _a, _b: 0.0)

    policy = RetryPolicy(max_attempts=3)
    call_count = 0

    @policy.retry(on=(ValueError,))
    def raise_type_error():
        nonlocal call_count
        call_count += 1
        raise TypeError("wrong type")

    with pytest.raises(TypeError):
        raise_type_error()
    # TypeError is not in `on=`, so no retry — called only once.
    assert call_count == 1


def test_retry_decorator_with_custom_should_retry(monkeypatch):
    """A custom should_retry callback can suppress retries."""
    monkeypatch.setattr("api_client_kit.retry.time.sleep", lambda _: None)
    monkeypatch.setattr("api_client_kit.retry.random.uniform", lambda _a, _b: 0.0)

    policy = RetryPolicy(max_attempts=5)
    call_count = 0

    @policy.retry(should_retry=lambda exc: "retry" in str(exc))
    def selective():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ValueError("please retry")
        raise ValueError("give up")

    with pytest.raises(ValueError, match="give up"):
        selective()
    assert call_count == 2


def test_retry_decorator_preserves_function_name():
    """functools.wraps preserves the original function metadata."""
    policy = RetryPolicy()

    @policy.retry
    def my_function():
        pass

    assert my_function.__name__ == "my_function"


# ---------------------------------------------------------------------------
# async_retry decorator
# ---------------------------------------------------------------------------

def test_async_retry_retries_then_succeeds(monkeypatch):
    """Async decorator retries and eventually returns."""
    monkeypatch.setattr("api_client_kit.retry.random.uniform", lambda _a, _b: 0.0)

    policy = RetryPolicy(max_attempts=3, base_delay_s=0)
    call_count = 0

    @policy.async_retry
    async def flaky():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise OSError("transient")
        return "done"

    result = asyncio.run(flaky())
    assert result == "done"
    assert call_count == 3


def test_async_retry_raises_after_exhaustion(monkeypatch):
    """Async decorator raises after all attempts are spent."""
    monkeypatch.setattr("api_client_kit.retry.random.uniform", lambda _a, _b: 0.0)

    policy = RetryPolicy(max_attempts=2, base_delay_s=0)

    @policy.async_retry
    async def always_fail():
        raise IOError("no luck")

    with pytest.raises(IOError, match="no luck"):
        asyncio.run(always_fail())


# ---------------------------------------------------------------------------
# should_retry override
# ---------------------------------------------------------------------------

def test_should_retry_default_returns_true():
    policy = RetryPolicy()
    assert policy.should_retry(ValueError("x")) is True
