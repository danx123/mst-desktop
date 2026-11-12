"""AppController: the single source of UI state (Android ViewModel equivalent).

Owns the active satellite, observer location, live position ticker, ground
track, pass predictions and CelesTrak sync. Pages only observe its signals.
"""
from __future__ import annotations

import time
from typing import Callable, Optional

from PySide6.QtCore import QObject, QRunnable, QSettings, QThreadPool, QTimer, Signal

from mst.i18n import tr
from mst.core.models import (
    GroundTrackPoint,
    ObserverLocation,
    PassPrediction,
    Satellite,
    SatellitePosition,
)
from mst.core.passes import PassPredictor
from mst.core.propagator import OrbitPropagator
from mst.core.tle import ParsedTle, parse_tle
from mst.data.repository import SatelliteRepository

_PASS_HOURS = 48
_MIN_ELEVATION = 10.0
_TRACK_REFRESH_TICKS = 30


class _WorkerSignals(QObject):
    finished = Signal(object, object)  # token, result
    failed = Signal(object, str)  # token, message


class _Worker(QRunnable):
    def __init__(self, token: object, fn: Callable[[], object]) -> None:
        super().__init__()
        self.token = token
        self.fn = fn
        self.signals = _WorkerSignals()

    def run(self) -> None:  # runs on a pool thread
        try:
            result = self.fn()
        except Exception as exc:  # noqa: BLE001 - surfaced to the UI
            self.signals.failed.emit(self.token, str(exc) or exc.__class__.__name__)
        else:
            self.signals.finished.emit(self.token, result)


class AppController(QObject):
    catalog_changed = Signal()
    active_satellite_changed = Signal(object)  # Satellite | None
    position_updated = Signal(object)  # SatellitePosition | None
    ground_track_updated = Signal(object)  # list[GroundTrackPoint]
    passes_updated = Signal(object)  # list[PassPrediction]
    passes_calculating = Signal(bool)
    observer_changed = Signal(object)  # ObserverLocation
    selected_pass_changed = Signal(object)  # PassPrediction | None
    syncing_changed = Signal(bool)
    sync_message_changed = Signal(str)  # "" = hidden

    def __init__(self, repository: SatelliteRepository, parent: Optional[QObject] = None) -> None:
        super().__init__(parent)
        self._repo = repository
        self._propagator = OrbitPropagator()
        self._predictor = PassPredictor(self._propagator)
        self._settings = QSettings("MacanAngkasa", "MST")

        self._satellites: list[Satellite] = []
        self._by_id: dict[int, Satellite] = {}
        self._active: Optional[Satellite] = None
        self._tle: Optional[ParsedTle] = None
        self._position: Optional[SatellitePosition] = None
        self._track: list[GroundTrackPoint] = []
        self._passes: list[PassPrediction] = []
        self._selected_pass: Optional[PassPrediction] = None
        self._observer = self._load_observer()

        self._syncing = False
        self._pass_generation = 0
        self._workers: dict[object, _Worker] = {}
        self._tick_count = 0

        self._timer = QTimer(self)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)

    # ------------------------------------------------------------------ state
    @property
    def satellites(self) -> list[Satellite]:
        return self._satellites

    @property
    def observer(self) -> ObserverLocation:
        return self._observer

    @property
    def active_satellite(self) -> Optional[Satellite]:
        return self._active

    @property
    def parsed_tle(self) -> Optional[ParsedTle]:
        return self._tle

    @property
    def position(self) -> Optional[SatellitePosition]:
        return self._position

    @property
    def ground_track(self) -> list[GroundTrackPoint]:
        return self._track

    @property
    def passes(self) -> list[PassPrediction]:
        return self._passes

    @property
    def selected_pass(self) -> Optional[PassPrediction]:
        return self._selected_pass

    @property
    def is_syncing(self) -> bool:
        return self._syncing

    def quick_satellites(self, limit: int = 8) -> list[Satellite]:
        """Favorites first (catalog order), used by the map's quick selector."""
        return self._satellites[:limit]

    def tle_age_days(self) -> Optional[float]:
        if self._tle is None:
            return None
        return self._tle.age_days(int(time.time() * 1000))

    # -------------------------------------------------------------- lifecycle
    def start(self) -> None:
        self._repo.seed_defaults_if_empty()
        self._reload_catalog()
        self.observer_changed.emit(self._observer)

        last = self._settings.value("active_norad", 0, type=int)
        candidate = (
            self._by_id.get(last)
            or self._by_id.get(57053)
            or self._by_id.get(25544)
            or (self._satellites[0] if self._satellites else None)
        )
        if candidate is not None:
            self.select_satellite(candidate)
        self._timer.start()

    def stop(self) -> None:
        self._timer.stop()
        self._pass_generation += 1  # discard in-flight results

    # --------------------------------------------------------------- commands
    def select_satellite(self, satellite: Satellite) -> None:
        satellite = self._by_id.get(satellite.norad_id, satellite)
        self._active = satellite
        self._tle = parse_tle(satellite.name, satellite.line1, satellite.line2)
        self._settings.setValue("active_norad", satellite.norad_id)

        self._passes = []
        self._selected_pass = None
        self.selected_pass_changed.emit(None)
        self.passes_updated.emit([])
        self.active_satellite_changed.emit(satellite)

        if self._tle is None:
            self._position = None
            self._track = []
            self.position_updated.emit(None)
            self.ground_track_updated.emit([])
            return

        self._refresh_position(refresh_track=True)
        self.calculate_passes()

    def toggle_favorite(self, norad_id: int) -> None:
        self._repo.toggle_favorite(norad_id)
        self._reload_catalog()
        if self._active is not None and self._active.norad_id == norad_id:
            self._active = self._by_id.get(norad_id, self._active)
            self.active_satellite_changed.emit(self._active)

    def set_observer(self, latitude: float, longitude: float, altitude_m: float = 10.0, name: str = "") -> None:
        name = name or tr("loc.custom")
        self._observer = ObserverLocation(
            max(-90.0, min(90.0, latitude)),
            ((longitude + 180.0) % 360.0) - 180.0,
            altitude_m,
            name,
        )
        self._save_observer()
        self.observer_changed.emit(self._observer)
        if self._tle is not None:
            self._refresh_position(refresh_track=False)
            self.calculate_passes()

    def select_pass(self, prediction: Optional[PassPrediction]) -> None:
        self._selected_pass = prediction
        self.selected_pass_changed.emit(prediction)

    def pass_path(self, prediction: PassPrediction) -> list[tuple[float, float]]:
        if self._tle is None:
            return []
        return self._predictor.pass_path(
            self._tle, self._observer, prediction.aos_time_millis, prediction.los_time_millis
        )

    def calculate_passes(self) -> None:
        tle = self._tle
        if tle is None:
            return
        self._pass_generation += 1
        generation = self._pass_generation
        observer = self._observer
        now = int(time.time() * 1000)

        worker = _Worker(
            ("passes", generation),
            lambda: self._predictor.predict(tle, observer, now, _PASS_HOURS, _MIN_ELEVATION),
        )
        worker.signals.finished.connect(self._on_passes_done)
        worker.signals.failed.connect(self._on_worker_failed)
        self._workers[worker.token] = worker
        self.passes_calculating.emit(True)
        QThreadPool.globalInstance().start(worker)

    def sync_celestrak(self, group: str, category: str) -> None:
        if self._syncing:
            return
        self._syncing = True
        self.syncing_changed.emit(True)
        self.sync_message_changed.emit(tr("sync.downloading", category=category))

        worker = _Worker(("sync", group), lambda: self._repo.sync_from_celestrak(group, category))
        worker.signals.finished.connect(lambda token, result, c=category: self._on_sync_done(token, result, c))
        worker.signals.failed.connect(self._on_worker_failed)
        self._workers[worker.token] = worker
        QThreadPool.globalInstance().start(worker)

    # ---------------------------------------------------------------- internals
    def _reload_catalog(self) -> None:
        self._satellites = self._repo.all()
        self._by_id = {s.norad_id: s for s in self._satellites}
        self.catalog_changed.emit()

    def _refresh_position(self, refresh_track: bool) -> None:
        if self._tle is None:
            return
        now = int(time.time() * 1000)
        self._position = self._propagator.position(self._tle, now, self._observer)
        self.position_updated.emit(self._position)
        if refresh_track or not self._track:
            self._track = self._propagator.ground_track(self._tle, now, 90, 90)
            self.ground_track_updated.emit(self._track)

    def _tick(self) -> None:
        if self._tle is None:
            return
        self._tick_count += 1
        self._refresh_position(refresh_track=self._tick_count % _TRACK_REFRESH_TICKS == 0)

    def _on_passes_done(self, token: object, result: object) -> None:
        self._workers.pop(token, None)
        if token != ("passes", self._pass_generation):
            return  # stale result from an earlier satellite/location
        self._passes = list(result)  # type: ignore[arg-type]
        self.passes_calculating.emit(False)
        self.passes_updated.emit(self._passes)

    def _on_sync_done(self, token: object, result: object, category: str) -> None:
        self._workers.pop(token, None)
        self._reload_catalog()
        self.sync_message_changed.emit(tr("sync.success", count=result, category=category))
        # Re-select the active satellite so it picks up its fresh TLE.
        if self._active is not None and self._active.norad_id in self._by_id:
            self.select_satellite(self._by_id[self._active.norad_id])
        QTimer.singleShot(3500, self._finish_sync)

    def _on_worker_failed(self, token: object, message: str) -> None:
        self._workers.pop(token, None)
        if isinstance(token, tuple) and token and token[0] == "passes":
            if token == ("passes", self._pass_generation):
                self.passes_calculating.emit(False)
            return
        self.sync_message_changed.emit(tr("sync.failed", message=message or tr("err.connection")))
        QTimer.singleShot(3500, self._finish_sync)

    def _finish_sync(self) -> None:
        self.sync_message_changed.emit("")
        self._syncing = False
        self.syncing_changed.emit(False)

    def _load_observer(self) -> ObserverLocation:
        s = self._settings
        if s.contains("observer/lat"):
            return ObserverLocation(
                s.value("observer/lat", -6.2088, type=float),
                s.value("observer/lon", 106.8456, type=float),
                s.value("observer/alt", 10.0, type=float),
                s.value("observer/name", "Jakarta, ID", type=str),
            )
        return ObserverLocation()

    def _save_observer(self) -> None:
        o = self._observer
        self._settings.setValue("observer/lat", o.latitude)
        self._settings.setValue("observer/lon", o.longitude)
        self._settings.setValue("observer/alt", o.altitude_m)
        self._settings.setValue("observer/name", o.name)
