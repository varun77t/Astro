"""Daily allowances per caller, so one visitor can't spend everyone's free LLM quota.

Only fresh AI-written readings count: cached ones and rule-only answers are free. Counted in
memory per process, which suits a single free-tier instance; a restart resets the counts.
"""

import threading
import time
from collections.abc import Callable
from datetime import UTC, datetime


class DailyQuota:
    def __init__(self, clock: Callable[[], float] = time.time):
        self._clock = clock
        self._day = ""
        self._used: dict[str, int] = {}
        self._lock = threading.Lock()

    def _roll(self) -> None:
        today = datetime.fromtimestamp(self._clock(), UTC).date().isoformat()
        if today != self._day:
            self._day, self._used = today, {}

    def remaining(self, key: str, limit: int) -> int:
        with self._lock:
            self._roll()
            return max(0, limit - self._used.get(key, 0))

    def spend(self, key: str) -> None:
        with self._lock:
            self._roll()
            self._used[key] = self._used.get(key, 0) + 1
