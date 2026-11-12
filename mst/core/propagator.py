"""Orbit propagation: Keplerian motion with J2 secular perturbations.

This is a simplified model (no drag, no deep-space terms), not full SGP4.
Accuracy degrades as the TLE gets older, so keep the catalog synced.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from mst.core.constants import EARTH_RADIUS_KM, J2, MU, TWO_PI
from mst.core.geo import ObserverFrame, gmst_rad, subpoint
from mst.core.models import GroundTrackPoint, ObserverLocation, SatellitePosition
from mst.core.tle import ParsedTle


@dataclass(frozen=True)
class EcefState:
    x: float
    y: float
    z: float
    r: float  # distance from Earth's centre, km


def solve_kepler(mean_anomaly: float, e: float) -> float:
    big_e = mean_anomaly if e < 0.8 else math.pi
    for _ in range(11):
        f = big_e - e * math.sin(big_e) - mean_anomaly
        f_prime = 1.0 - e * math.cos(big_e)
        delta = f / f_prime
        big_e -= delta
        if abs(delta) < 1e-8:
            break
    return big_e


class OrbitPropagator:
    def propagate_ecef(self, tle: ParsedTle, time_millis: int) -> EcefState:
        dt = (time_millis - tle.epoch_millis) / 1000.0
        e = tle.eccentricity
        a = tle.semi_major_axis_km
        n = tle.mean_motion_rad_per_sec

        p = a * (1.0 - e * e)
        j2_term = 1.5 * J2 * (EARTH_RADIUS_KM / p) ** 2 * n
        cos_i = math.cos(tle.inclination_rad)
        sin_i = math.sin(tle.inclination_rad)

        raan_dot = -j2_term * cos_i
        arg_perigee_dot = 0.5 * j2_term * (5.0 * cos_i * cos_i - 1.0)

        raan = math.fmod(tle.raan_rad + raan_dot * dt, TWO_PI)
        arg_perigee = math.fmod(tle.arg_perigee_rad + arg_perigee_dot * dt, TWO_PI)
        mean_anomaly = math.fmod(tle.mean_anomaly_rad + n * dt, TWO_PI)

        big_e = solve_kepler(mean_anomaly, e)
        cos_e, sin_e = math.cos(big_e), math.sin(big_e)
        denom = 1.0 - e * cos_e

        sin_nu = math.sqrt(1.0 - e * e) * sin_e / denom
        cos_nu = (cos_e - e) / denom
        nu = math.atan2(sin_nu, cos_nu)

        r = a * denom
        u = arg_perigee + nu
        cu, su = math.cos(u), math.sin(u)
        cr, sr = math.cos(raan), math.sin(raan)

        x_eci = r * (cu * cr - su * sr * cos_i)
        y_eci = r * (cu * sr + su * cr * cos_i)
        z_eci = r * su * sin_i

        g = gmst_rad(time_millis)
        cg, sg = math.cos(g), math.sin(g)
        x_ecef = x_eci * cg + y_eci * sg
        y_ecef = -x_eci * sg + y_eci * cg
        return EcefState(x_ecef, y_ecef, z_eci, r)

    def position(self, tle: ParsedTle, time_millis: int, observer: ObserverLocation) -> SatellitePosition:
        state = self.propagate_ecef(tle, time_millis)
        lat, lon, altitude = subpoint(state.x, state.y, state.z, state.r)

        velocity = math.sqrt(MU * (2.0 / state.r - 1.0 / tle.semi_major_axis_km))
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
            velocity_km_s=velocity,
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
            s = self.propagate_ecef(tle, t)
            lat, lon, alt = subpoint(s.x, s.y, s.z, s.r)
            points.append(GroundTrackPoint(lat, lon, alt, t))
        return points
