from __future__ import annotations
import random, time
from dataclasses import dataclass

@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    base_delay_s: float = 0.5
    max_delay_s: float = 8.0
    jitter: float = 0.2

    def backoff_sleep(self, attempt: int) -> None:
        raw = min(self.max_delay_s, self.base_delay_s * (2 ** (attempt - 1)))
        raw *= 1.0 + random.uniform(-self.jitter, self.jitter)
        time.sleep(max(0.0, raw))
