"""A small, strict rate limiter for public government endpoints.

The services in this package are free, public and maintained by tax
authorities for one at a time verification. They are not a bulk data source.
Hammering them gets your IP blocked, degrades a service other people depend
on, and is the fastest way to lose access to something you cannot buy back.

The rule applied throughout this library: one request at a time, a floor on
the interval between requests, exponential backoff on any 429 or 5xx, and a
hard stop rather than a retry storm. If you need ten thousand checks, run
them over days, cache aggressively, and re validate on a TTL rather than on
every pipeline run.
"""

from __future__ import annotations

import random
import threading
import time
from dataclasses import dataclass, field


@dataclass
class RateLimiter:
    """Blocking limiter that guarantees a minimum gap between calls."""

    min_interval: float = 1.0
    jitter: float = 0.25
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)
    _last: float = field(default=0.0, repr=False)

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            gap = self.min_interval + random.uniform(0, self.jitter)
            sleep_for = self._last + gap - now
            if sleep_for > 0:
                time.sleep(sleep_for)
            self._last = time.monotonic()


class Backoff:
    """Exponential backoff with a ceiling and a hard attempt limit."""

    def __init__(self, base: float = 2.0, cap: float = 300.0,
                 max_attempts: int = 5) -> None:
        self.base = base
        self.cap = cap
        self.max_attempts = max_attempts

    def delay(self, attempt: int) -> float:
        return min(self.cap, self.base * (2 ** max(0, attempt - 1)))

    def should_retry(self, attempt: int) -> bool:
        return attempt < self.max_attempts
