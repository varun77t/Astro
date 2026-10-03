"""Narrated readings and provider usage, in SQLite.

Stand-in for the `readings` Supabase table (Phase 7). Rows are keyed by a hash of exactly
what was sent to the model (chart facts, matched rules, area, language, rules and prompt
versions), so they hold no personal data and can be shared by everyone whose chart says the
same thing. Usage rows record provider, outcome and latency, never prompt contents.
"""

import json
import sqlite3
import threading
import time
from pathlib import Path

from app.llm.router import Attempt


class ReadingCache:
    def __init__(self, path: str):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.executescript(
            "CREATE TABLE IF NOT EXISTS readings ("
            " input_hash TEXT PRIMARY KEY, area TEXT NOT NULL, language TEXT NOT NULL,"
            " rules_version TEXT NOT NULL, content_json TEXT NOT NULL, provider TEXT NOT NULL,"
            " model TEXT NOT NULL, created_at REAL NOT NULL);"
            "CREATE TABLE IF NOT EXISTS llm_usage ("
            " provider TEXT NOT NULL, model TEXT NOT NULL, outcome TEXT NOT NULL,"
            " latency_ms INTEGER NOT NULL, created_at REAL NOT NULL);"
        )
        self._db.commit()

    def get(self, input_hash: str) -> tuple[dict, str, str] | None:
        """(content, provider, model) for a previous identical request."""
        with self._lock:
            row = self._db.execute(
                "SELECT content_json, provider, model FROM readings WHERE input_hash = ?",
                (input_hash,),
            ).fetchone()
        return (json.loads(row[0]), row[1], row[2]) if row else None

    def set(
        self,
        input_hash: str,
        *,
        area: str,
        language: str,
        rules_version: str,
        content: dict,
        provider: str,
        model: str,
    ) -> None:
        with self._lock:
            self._db.execute(
                "INSERT OR REPLACE INTO readings VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    input_hash,
                    area,
                    language,
                    rules_version,
                    json.dumps(content),
                    provider,
                    model,
                    time.time(),
                ),
            )
            self._db.commit()

    def record(self, attempt: Attempt) -> None:
        with self._lock:
            self._db.execute(
                "INSERT INTO llm_usage VALUES (?, ?, ?, ?, ?)",
                (attempt.provider, attempt.model, attempt.outcome, attempt.latency_ms, time.time()),
            )
            self._db.commit()

    def usage_today(self) -> dict[str, dict[str, int]]:
        """Calls per provider and outcome since midnight UTC."""
        midnight = time.time() - time.time() % 86400
        with self._lock:
            rows = self._db.execute(
                "SELECT provider, outcome, COUNT(*) FROM llm_usage WHERE created_at >= ?"
                " GROUP BY provider, outcome",
                (midnight,),
            ).fetchall()
        out: dict[str, dict[str, int]] = {}
        for provider, outcome, n in rows:
            out.setdefault(provider, {})[outcome] = n
        return out
