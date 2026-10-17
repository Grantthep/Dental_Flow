"""In-memory login rate limit (one backend process; move to Redis if we ever run several)."""

import os
import time
from collections import defaultdict, deque
from threading import Lock

MAX_FAILURES = int(os.getenv("LOGIN_MAX_FAILURES", "5"))
WINDOW_SECONDS = int(os.getenv("LOGIN_WINDOW_SECONDS", "900"))


class LoginLimiter:
    def __init__(self, max_failures: int = MAX_FAILURES, window: int = WINDOW_SECONDS):
        self.max_failures, self.window = max_failures, window
        self._failures: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def _recent(self, key: str) -> deque[float]:
        q, cutoff = self._failures[key], time.monotonic() - self.window
        while q and q[0] < cutoff:
            q.popleft()
        return q

    def retry_after(self, key: str) -> int:
        """Seconds until `key` may try again; 0 if not blocked."""
        with self._lock:
            q = self._recent(key)
            if len(q) < self.max_failures:
                return 0
            return max(1, int(q[0] + self.window - time.monotonic()))

    def fail(self, key: str) -> None:
        with self._lock:
            self._recent(key).append(time.monotonic())

    def reset(self, key: str | None = None) -> None:
        with self._lock:
            if key is None:
                self._failures.clear()
            else:
                self._failures.pop(key, None)


login_limiter = LoginLimiter()
