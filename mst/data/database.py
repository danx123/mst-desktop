"""SQLite persistence for the satellite catalog."""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

from mst.core.models import Satellite

_SCHEMA = """
CREATE TABLE IF NOT EXISTS satellites (
    norad_id     INTEGER PRIMARY KEY,
    name         TEXT    NOT NULL,
    line1        TEXT    NOT NULL,
    line2        TEXT    NOT NULL,
    category     TEXT    NOT NULL,
    is_favorite  INTEGER NOT NULL DEFAULT 0,
    last_updated INTEGER NOT NULL
)
"""

# On conflict: refresh TLE data but keep the user's favorite flag, and never
# demote an INDONESIA satellite into a generic group (e.g. when it also
# appears in the GEO feed).
_UPSERT = """
INSERT INTO satellites (norad_id, name, line1, line2, category, is_favorite, last_updated)
VALUES (?, ?, ?, ?, ?, ?, ?)
ON CONFLICT(norad_id) DO UPDATE SET
    name = excluded.name,
    line1 = excluded.line1,
    line2 = excluded.line2,
    last_updated = excluded.last_updated,
    category = CASE WHEN satellites.category = 'INDONESIA'
                    THEN satellites.category ELSE excluded.category END
"""


def _row_to_satellite(row: sqlite3.Row) -> Satellite:
    return Satellite(
        norad_id=row["norad_id"],
        name=row["name"],
        line1=row["line1"],
        line2=row["line2"],
        category=row["category"],
        is_favorite=bool(row["is_favorite"]),
        last_updated=row["last_updated"],
    )


class SatelliteDatabase:
    """Thread-safe (single connection guarded by a lock) catalog store."""

    def __init__(self, path: Path | str) -> None:
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        with self._lock:
            self._conn.execute(_SCHEMA)
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def count(self) -> int:
        with self._lock:
            return self._conn.execute("SELECT COUNT(*) FROM satellites").fetchone()[0]

    def all(self) -> list[Satellite]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM satellites ORDER BY is_favorite DESC, name ASC"
            ).fetchall()
        return [_row_to_satellite(r) for r in rows]

    def get(self, norad_id: int) -> Satellite | None:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM satellites WHERE norad_id = ?", (norad_id,)
            ).fetchone()
        return _row_to_satellite(row) if row else None

    def upsert_many(self, satellites: list[Satellite]) -> None:
        data = [
            (s.norad_id, s.name, s.line1, s.line2, s.category, int(s.is_favorite), s.last_updated)
            for s in satellites
        ]
        with self._lock:
            self._conn.executemany(_UPSERT, data)
            self._conn.commit()

    def set_favorite(self, norad_id: int, favorite: bool) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE satellites SET is_favorite = ? WHERE norad_id = ?",
                (int(favorite), norad_id),
            )
            self._conn.commit()
