"""Per-provider request budgets: requests per minute, requests per UTC day, and cool-downs.

Counted in this process only. That's enough for one API instance on a free host; the usage
table in the readings cache keeps a durable record for checking how close we run to limits.
"""

import threading
import time
from collections import deque
from collections.abc import Callable
from datetime import UTC, datetime


class RateLimiter:
    def __init__(
        self,
        rpm: int,
        rpd: int,
        tpm: int | None = None,
        clock: Callable[[], float] = time.time,
    ):
        self.rpm, self.rpd, self.tpm = rpm, rpd, tpm
        self._clock = clock
        self._minute: deque[tuple[float, int]] = deque()  # (time, estimated tokens)
        self._day = ""
        self._day_count = 0
        self._cool_until = 0.0
        self._lock = threading.Lock()

    def _today(self, now: float) -> str:
        return datetime.fromtimestamp(now, UTC).date().isoformat()

    def try_acquire(self, tokens: int = 0) -> bool:
        """Take one request (of about `tokens` tokens) from the budget, or say no at once."""
        with self._lock:
            now = self._clock()
            if now < self._cool_until:
                return False
            while self._minute and now - self._minute[0][0] >= 60:
                self._minute.popleft()
            if self._today(now) != self._day:
                self._day, self._day_count = self._today(now), 0
            if len(self._minute) >= self.rpm or self._day_count >= self.rpd:
                return False
            if self.tpm is not None and sum(t for _, t in self._minute) + tokens > self.tpm:
                return False
            self._minute.append((now, tokens))
            self._day_count += 1
            return True

    def wait_seconds(self) -> float:
        """Roughly how long until this provider could take a request again."""
        with self._lock:
            now = self._clock()
            if self._day_count >= self.rpd and self._today(now) == self._day:
                return 86400 - now % 86400  # until midnight UTC
            waits = [self._cool_until - now]
            if self._minute:
                waits.append(60 - (now - self._minute[0][0]))
            return max(0.0, *waits)

    def cool_down(self, seconds: float) -> None:
        with self._lock:
            self._cool_until = max(self._cool_until, self._clock() + seconds)

    @property
    def cooling(self) -> bool:
        return self._clock() < self._cool_until
