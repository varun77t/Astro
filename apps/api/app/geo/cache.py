"""Geocode result cache in SQLite.

Stand-in for the `geocode_cache` Supabase table (Phase 7). Entries hold only place
search strings and public place data, no personal data.
"""

import json
import sqlite3
import threading
import time
from pathlib import Path

from app.schemas.geo import Place


class GeocodeCache:
    def __init__(self, path: str, ttl_days: int = 30):
        if path != ":memory:":
            Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._ttl_seconds = ttl_days * 86400
        self._lock = threading.Lock()
        self._db = sqlite3.connect(path, check_same_thread=False)
        self._db.execute(
            "CREATE TABLE IF NOT EXISTS geocode_cache ("
            " query TEXT NOT NULL, lang TEXT NOT NULL, results_json TEXT NOT NULL,"
            " created_at REAL NOT NULL, PRIMARY KEY (query, lang))"
        )
        self._db.commit()

    def get(self, query: str, lang: str) -> list[Place] | None:
        with self._lock:
            row = self._db.execute(
                "SELECT results_json, created_at FROM geocode_cache WHERE query = ? AND lang = ?",
                (query, lang),
            ).fetchone()
        if row is None or time.time() - row[1] > self._ttl_seconds:
            return None
        return [Place.model_validate(item) for item in json.loads(row[0])]

    def set(self, query: str, lang: str, places: list[Place]) -> None:
        payload = json.dumps([p.model_dump() for p in places])
        with self._lock:
            self._db.execute(
                "INSERT OR REPLACE INTO geocode_cache VALUES (?, ?, ?, ?)",
                (query, lang, payload, time.time()),
            )
            self._db.commit()
