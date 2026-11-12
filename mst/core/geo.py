"""Geodesy helpers: sidereal time, sub-satellite point, topocentric look angles."""
from __future__ import annotations

import math

from mst.core.constants import (
    DEG_TO_RAD,
    EARTH_E2,
    EARTH_FLATTENING,
    EARTH_RADIUS_KM,
    RAD_TO_DEG,
)
from mst.core.models import ObserverLocation


def gmst_rad(time_millis: int) -> float:
    """Greenwich Mean Sidereal Time (radians) for a UNIX time in milliseconds."""
    julian_date = 2440587.5 + time_millis / 86_400_000.0
    d = julian_date - 2451545.0
    gmst_deg = (280.46061837 + 360.98564736629 * d) % 360.0
    return gmst_deg * DEG_TO_RAD


def subpoint(x: float, y: float, z: float, r: float) -> tuple[float, float, float]:
    """ECEF -> (latitude_deg, longitude_deg, altitude_km)."""
    lon_deg = math.atan2(y, x) * RAD_TO_DEG
    d_plane = math.hypot(x, y)
    lat_rad = math.atan2(z, d_plane * (1.0 - EARTH_FLATTENING))
    sin_lat = math.sin(lat_rad)
    radius_at_lat = EARTH_RADIUS_KM / math.sqrt(1.0 - EARTH_E2 * sin_lat * sin_lat)
    altitude = max(100.0, r - radius_at_lat)
    return lat_rad * RAD_TO_DEG, lon_deg, altitude


class ObserverFrame:
    """Precomputed ECEF position and local ENU basis of an observer."""

    def __init__(self, observer: ObserverLocation) -> None:
        lat = observer.latitude * DEG_TO_RAD
        lon = observer.longitude * DEG_TO_RAD
        alt_km = observer.altitude_m / 1000.0

        self._sin_lat = math.sin(lat)
        self._cos_lat = math.cos(lat)
        self._sin_lon = math.sin(lon)
        self._cos_lon = math.cos(lon)

        n = EARTH_RADIUS_KM / math.sqrt(1.0 - EARTH_E2 * self._sin_lat**2)
        self._x = (n + alt_km) * self._cos_lat * self._cos_lon
        self._y = (n + alt_km) * self._cos_lat * self._sin_lon
        self._z = (n * (1.0 - EARTH_E2) + alt_km) * self._sin_lat

    def look(self, sat_x: float, sat_y: float, sat_z: float) -> tuple[float, float, float]:
        """Return (azimuth_deg, elevation_deg, range_km) toward an ECEF point."""
        dx = sat_x - self._x
        dy = sat_y - self._y
        dz = sat_z - self._z

        sl, cl = self._sin_lat, self._cos_lat
        so, co = self._sin_lon, self._cos_lon

        south = sl * co * dx + sl * so * dy - cl * dz
        north = -south
        east = -so * dx + co * dy
        up = cl * co * dx + cl * so * dy + sl * dz

        rng = math.sqrt(dx * dx + dy * dy + dz * dz)
        horiz = math.hypot(north, east)
        elevation = math.atan2(up, horiz) * RAD_TO_DEG
        azimuth = (math.atan2(east, north) * RAD_TO_DEG) % 360.0
        return azimuth, elevation, rng
