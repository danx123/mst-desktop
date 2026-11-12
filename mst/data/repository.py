"""Repository: single entry point the UI layer uses for satellite data."""
from __future__ import annotations

from typing import Callable, Optional

from mst.core.models import Satellite
from mst.data import celestrak
from mst.data.database import SatelliteDatabase
from mst.data.default_satellites import default_satellites

FetchFn = Callable[[str, str], list[Satellite]]


class SatelliteRepository:
    def __init__(self, database: SatelliteDatabase, fetch: Optional[FetchFn] = None) -> None:
        self._db = database
        self._fetch = fetch or celestrak.fetch_group

    def all(self) -> list[Satellite]:
        return self._db.all()

    def seed_defaults_if_empty(self) -> None:
        if self._db.count() == 0:
            self._db.upsert_many(default_satellites())

    def toggle_favorite(self, norad_id: int) -> None:
        current = self._db.get(norad_id)
        if current is not None:
            self._db.set_favorite(norad_id, not current.is_favorite)

    def sync_from_celestrak(self, group: str, category: str) -> int:
        """Download a group and merge it into the catalog. Returns the count."""
        satellites = self._fetch(group, category)
        self._db.upsert_many(satellites)
        return len(satellites)
