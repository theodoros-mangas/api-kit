
from __future__ import annotations

import asyncio
import functools
import logging
import random
import time
from dataclasses import dataclass
from typing import Any, Callable, Optional, Tuple, Type, TypeVar

T = TypeVar("T")

logger = logging.getLogger(__name__)

# Default set of transient exceptions worth retrying (extend as needed).
RETRYABLE_EXCEPTIONS: Tuple[Type[BaseException], ...] = (
    Exception,
)


@dataclass(frozen=True)
class RetryPolicy:
    """Retry policy with exponential backoff and jitter.

    Used by ``APIClient._request`` to decide how many times to retry and
    how long to sleep between attempts.  Also exposes ``retry`` /
    ``async_retry`` decorators for wrapping arbitrary callables.
    """

    max_attempts: int = 3
    base_delay_s: float = 0.5
    max_delay_s: float = 8.0
    jitter: float = 0.2

    # --- delay helpers ---------------------------------------------------

    def _compute_delay(self, attempt: int) -> float:
        """Return the delay in seconds for the given *attempt* (1-based)."""
        raw = min(self.max_delay_s, self.base_delay_s * (2 ** (attempt - 1)))
        raw *= 1.0 + random.uniform(-self.jitter, self.jitter)
        return max(0.0, raw)

    def backoff_sleep(self, attempt: int) -> None:
        """Synchronous sleep with exponential backoff."""
        time.sleep(self._compute_delay(attempt))

    async def async_backoff_sleep(self, attempt: int) -> None:
        """Asynchronous sleep with exponential backoff."""
        await asyncio.sleep(self._compute_delay(attempt))

    # --- retryable check -------------------------------------------------

    def should_retry(self, exc: BaseException) -> bool:
        """Return ``True`` if *exc* should trigger a retry.

        The default implementation always returns ``True``; subclass and
        override to restrict which errors are retryable.
        """
        return True

    # --- sync decorator --------------------------------------------------

    def retry(
        self,
        func: Optional[Callable[..., T]] = None,
        *,
        on: Tuple[Type[BaseException], ...] = RETRYABLE_EXCEPTIONS,
        should_retry: Optional[Callable[[BaseException], bool]] = None,
    ) -> Any:
        """Decorator that retries *func* according to this policy.

        Can be used with or without arguments::

            policy = RetryPolicy()

            @policy.retry
            def fetch(): ...

            @policy.retry(on=(httpx.TimeoutException,))
            def fetch(): ...
        """
        def decorator(fn: Callable[..., T]) -> Callable[..., T]:
            @functools.wraps(fn)
            def wrapper(*args: Any, **kwargs: Any) -> T:
                last_exc: Optional[BaseException] = None
                for attempt in range(1, self.max_attempts + 1):
                    try:
                        return fn(*args, **kwargs)
                    except on as exc:
                        last_exc = exc
                        do_retry = should_retry(exc) if should_retry else self.should_retry(exc)
                        if not do_retry or attempt == self.max_attempts:
                            logger.warning("Giving up after %d attempt(s): %s", attempt, exc)
                            break
                        logger.info("Attempt %d failed (%s), retrying…", attempt, exc)
                        self.backoff_sleep(attempt)
                raise last_exc  # type: ignore[misc]
            return wrapper

        # Allow bare ``@policy.retry`` (no parentheses).
        if func is not None:
            return decorator(func)
        return decorator

    # --- async decorator -------------------------------------------------

    def async_retry(
        self,
        func: Optional[Callable[..., Any]] = None,
        *,
        on: Tuple[Type[BaseException], ...] = RETRYABLE_EXCEPTIONS,
        should_retry: Optional[Callable[[BaseException], bool]] = None,
    ) -> Any:
        """Async equivalent of :meth:`retry`."""
        def decorator(fn: Callable[..., Any]) -> Callable[..., Any]:
            @functools.wraps(fn)
            async def wrapper(*args: Any, **kwargs: Any) -> Any:
                last_exc: Optional[BaseException] = None
                for attempt in range(1, self.max_attempts + 1):
                    try:
                        return await fn(*args, **kwargs)
                    except on as exc:
                        last_exc = exc
                        do_retry = should_retry(exc) if should_retry else self.should_retry(exc)
                        if not do_retry or attempt == self.max_attempts:
                            logger.warning("Giving up after %d attempt(s): %s", attempt, exc)
                            break
                        logger.info("Attempt %d failed (%s), retrying (async)…", attempt, exc)
                        await self.async_backoff_sleep(attempt)
                raise last_exc  # type: ignore[misc]
            return wrapper

        if func is not None:
            return decorator(func)
        return decorator
