"""Orbit propagation with the full SGP4 / SDP4 model (via the ``sgp4`` package).

The near-Earth (SGP4) and deep-space (SDP4: lunar-solar perturbations and
12 h / 24 h resonances) branches are selected automatically from the TLE's
orbital period. SGP4 works in the TEME frame; positions are rotated to ECEF
with GMST (polar motion and nutation are ignored, well below TLE accuracy).
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from mst.core.constants import EARTH_RADIUS_KM
from mst.core.geo import ObserverFrame, gmst_rad, subpoint
from mst.core.models import GroundTrackPoint, ObserverLocation, SatellitePosition
from mst.core.tle import ParsedTle

_MS_PER_DAY = 86_400_000.0

_SGP4_ERRORS = {
    1: "mean eccentricity outside 0..1",
    2: "mean motion is negative",
    3: "perturbed eccentricity outside 0..1",
    4: "semi-latus rectum is negative",
    5: "epoch elements are sub-orbital",
    6: "satellite has decayed",
}


class PropagationError(Exception):
    """SGP4 could not propagate this TLE to the requested time."""

    def __init__(self, code: int) -> None:
        self.code = code
        super().__init__(f"SGP4 error {code}: {_SGP4_ERRORS.get(code, 'unknown')}")


@dataclass(frozen=True)
class EcefState:
    x: float
    y: float
    z: float
    r: float  # distance from Earth's centre, km
    speed_km_s: float = 0.0  # inertial (TEME) speed


class OrbitPropagator:
    def propagate_teme(
        self, tle: ParsedTle, time_millis: int
    ) -> tuple[tuple[float, float, float], tuple[float, float, float]]:
        """SGP4/SDP4 position (km) and velocity (km/s) in the TEME frame."""
        days = time_millis / _MS_PER_DAY
        whole = math.floor(days)
        jd = 2440587.5 + whole  # UNIX epoch = JD 2440587.5
        fr = days - whole
        with tle.lock:
            error, r, v = tle.satrec.sgp4(jd, fr)
        if error:
            raise PropagationError(error)
        return r, v

    def propagate_ecef(self, tle: ParsedTle, time_millis: int) -> EcefState:
        (x, y, z), (vx, vy, vz) = self.propagate_teme(tle, time_millis)
        g = gmst_rad(time_millis)
        cg, sg = math.cos(g), math.sin(g)
        x_ecef = x * cg + y * sg
        y_ecef = -x * sg + y * cg
        r = math.sqrt(x * x + y * y + z * z)
        speed = math.sqrt(vx * vx + vy * vy + vz * vz)
        return EcefState(x_ecef, y_ecef, z, r, speed)

    def position(self, tle: ParsedTle, time_millis: int, observer: ObserverLocation) -> SatellitePosition:
        state = self.propagate_ecef(tle, time_millis)
        lat, lon, altitude = subpoint(state.x, state.y, state.z, state.r)

        period = 1440.0 / tle.mean_motion_rev_per_day

        horizon = math.acos(EARTH_RADIUS_KM / (EARTH_RADIUS_KM + altitude))
        footprint = EARTH_RADIUS_KM * horizon

        az, el, rng = ObserverFrame(observer).look(state.x, state.y, state.z)

        return SatellitePosition(
            norad_id=tle.norad_id,
            name=tle.name,
            latitude=lat,
            longitude=lon,
            altitude_km=altitude,
            velocity_km_s=state.speed_km_s,
            azimuth_deg=az,
            elevation_deg=el,
            range_km=rng,
            footprint_radius_km=footprint,
            period_minutes=period,
            timestamp_millis=time_millis,
            is_visible=el > 0.0,
        )

    def ground_track(
        self,
        tle: ParsedTle,
        start_millis: int,
        duration_minutes: int = 90,
        step_seconds: int = 60,
    ) -> list[GroundTrackPoint]:
        steps = (duration_minutes * 60) // step_seconds
        points: list[GroundTrackPoint] = []
        for i in range(steps + 1):
            t = start_millis + i * step_seconds * 1000
            try:
                s = self.propagate_ecef(tle, t)
            except PropagationError:
                continue  # skip samples past the point where the model breaks down
            lat, lon, alt = subpoint(s.x, s.y, s.z, s.r)
            points.append(GroundTrackPoint(lat, lon, alt, t))
        return points
