"""In-memory login rate limit (one backend process; move to Redis if we ever run several)."""

import os
import time
from collections import deque
from threading import Lock

MAX_FAILURES = int(os.getenv("LOGIN_MAX_FAILURES", "5"))
WINDOW_SECONDS = int(os.getenv("LOGIN_WINDOW_SECONDS", "900"))


class LoginLimiter:
    def __init__(self, max_failures: int = MAX_FAILURES, window: int = WINDOW_SECONDS):
        self.max_failures, self.window = max_failures, window
        self._failures: dict[str, deque[float]] = {}
        self._lock = Lock()
        self._next_sweep = time.monotonic() + window

    def _recent(self, key: str) -> deque[float]:
        """Failures for `key` inside the window. Never creates an entry, and drops it once it's empty,
        so lookups with random emails can't grow memory."""
        q, cutoff = self._failures.get(key), time.monotonic() - self.window
        if q is None:
            return deque()
        while q and q[0] < cutoff:
            q.popleft()
        if not q:
            del self._failures[key]
        return q

    def _sweep(self) -> None:
        """Once per window, forget keys whose failures have all expired (keys nobody asks about again)."""
        now = time.monotonic()
        if now >= self._next_sweep:
            for key in list(self._failures):
                self._recent(key)
            self._next_sweep = now + self.window

    def retry_after(self, key: str) -> int:
        """Seconds until `key` may try again; 0 if not blocked."""
        with self._lock:
            q = self._recent(key)
            if len(q) < self.max_failures:
                return 0
            return max(1, int(q[0] + self.window - time.monotonic()))

    def fail(self, key: str) -> None:
        with self._lock:
            self._sweep()
            self._failures.setdefault(key, self._recent(key)).append(time.monotonic())

    def reset(self, key: str | None = None) -> None:
        with self._lock:
            if key is None:
                self._failures.clear()
            else:
                self._failures.pop(key, None)


login_limiter = LoginLimiter()
