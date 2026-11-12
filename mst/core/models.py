"""Plain data models shared by every layer (no Qt imports here)."""
from __future__ import annotations

import time
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ObserverLocation:
    latitude: float = -6.2088  # Jakarta default
    longitude: float = 106.8456
    altitude_m: float = 10.0
    name: str = "Jakarta, ID"


@dataclass(frozen=True)
class Satellite:
    norad_id: int
    name: str
    line1: str
    line2: str
    category: str  # INDONESIA, STATIONS, WEATHER, STARLINK, GEO, OTHER
    is_favorite: bool = False
    last_updated: int = field(default_factory=lambda: int(time.time() * 1000))


@dataclass(frozen=True)
class SatellitePosition:
    norad_id: int
    name: str
    latitude: float  # deg
    longitude: float  # deg
    altitude_km: float
    velocity_km_s: float
    azimuth_deg: float  # topocentric, 0..360
    elevation_deg: float  # topocentric, -90..90
    range_km: float
    footprint_radius_km: float
    period_minutes: float
    timestamp_millis: int
    is_visible: bool  # elevation > 0


@dataclass(frozen=True)
class GroundTrackPoint:
    latitude: float
    longitude: float
    altitude_km: float
    timestamp_millis: int


@dataclass(frozen=True)
class PassPrediction:
    satellite_name: str
    norad_id: int
    aos_time_millis: int  # acquisition of signal
    max_elevation_time_millis: int
    los_time_millis: int  # loss of signal
    max_elevation_deg: float
    aos_azimuth_deg: float
    los_azimuth_deg: float
    max_azimuth_deg: float
    duration_seconds: int
