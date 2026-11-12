"""Pass prediction (AOS / peak / LOS) for an observer."""
from __future__ import annotations

from typing import Callable, Optional

from mst.core.geo import ObserverFrame
from mst.core.models import ObserverLocation, PassPrediction
from mst.core.propagator import OrbitPropagator
from mst.core.tle import ParsedTle


class PassPredictor:
    def __init__(self, propagator: Optional[OrbitPropagator] = None) -> None:
        self._prop = propagator or OrbitPropagator()

    # -- helpers ---------------------------------------------------------
    def _look(self, tle: ParsedTle, frame: ObserverFrame, t: int) -> tuple[float, float]:
        s = self._prop.propagate_ecef(tle, t)
        az, el, _ = frame.look(s.x, s.y, s.z)
        return az, el

    def _refine_crossing(self, tle: ParsedTle, frame: ObserverFrame, t_lo: int, t_hi: int, rising: bool) -> int:
        """Bisect the horizon crossing between two samples (~0.5 s resolution)."""
        for _ in range(6):
            mid = (t_lo + t_hi) // 2
            above = self._look(tle, frame, mid)[1] > 0.0
            if rising:
                if above:
                    t_hi = mid
                else:
                    t_lo = mid
            else:
                if above:
                    t_lo = mid
                else:
                    t_hi = mid
        return t_hi if rising else t_lo

    def _refine_peak(self, tle: ParsedTle, frame: ObserverFrame, lo: int, hi: int) -> tuple[int, float, float]:
        for _ in range(14):
            third = (hi - lo) // 3
            m1, m2 = lo + third, hi - third
            if self._look(tle, frame, m1)[1] < self._look(tle, frame, m2)[1]:
                lo = m1
            else:
                hi = m2
        t = (lo + hi) // 2
        az, el = self._look(tle, frame, t)
        return t, el, az

    # -- public API ------------------------------------------------------
    def predict(
        self,
        tle: ParsedTle,
        observer: ObserverLocation,
        start_millis: int,
        duration_hours: int = 48,
        min_elevation_deg: float = 10.0,
        step_seconds: int = 30,
        cancelled: Optional[Callable[[], bool]] = None,
    ) -> list[PassPrediction]:
        frame = ObserverFrame(observer)
        passes: list[PassPrediction] = []

        in_pass = False
        aos_t = 0
        aos_az = 0.0
        max_el = -90.0
        max_t = 0
        prev_t = start_millis
        step_ms = step_seconds * 1000

        for offset in range(0, duration_hours * 3600 + 1, step_seconds):
            if cancelled is not None and offset % 600 == 0 and cancelled():
                break

            t = start_millis + offset * 1000
            az, el = self._look(tle, frame, t)

            if el > 0.0:
                if not in_pass:
                    in_pass = True
                    if offset == 0:
                        aos_t, aos_az = t, az
                    else:
                        aos_t = self._refine_crossing(tle, frame, prev_t, t, rising=True)
                        aos_az = self._look(tle, frame, aos_t)[0]
                    max_el, max_t = el, t
                elif el > max_el:
                    max_el, max_t = el, t
            elif in_pass:
                in_pass = False
                los_t = self._refine_crossing(tle, frame, prev_t, t, rising=False)
                los_az = self._look(tle, frame, los_t)[0]
                duration = (los_t - aos_t) // 1000

                if max_el >= min_elevation_deg and duration > 60:
                    lo = max(aos_t, max_t - step_ms)
                    hi = min(los_t, max_t + step_ms)
                    peak_t, peak_el, peak_az = self._refine_peak(tle, frame, lo, hi)
                    passes.append(
                        PassPrediction(
                            satellite_name=tle.name,
                            norad_id=tle.norad_id,
                            aos_time_millis=aos_t,
                            max_elevation_time_millis=peak_t,
                            los_time_millis=los_t,
                            max_elevation_deg=max(peak_el, max_el),
                            aos_azimuth_deg=aos_az,
                            los_azimuth_deg=los_az,
                            max_azimuth_deg=peak_az,
                            duration_seconds=duration,
                        )
                    )
            prev_t = t
        return passes

    def pass_path(
        self,
        tle: ParsedTle,
        observer: ObserverLocation,
        aos_millis: int,
        los_millis: int,
        step_seconds: int = 10,
    ) -> list[tuple[float, float]]:
        """Sky-plot samples ``(azimuth_deg, elevation_deg)`` across a pass."""
        frame = ObserverFrame(observer)
        points: list[tuple[float, float]] = []
        t = aos_millis
        while t < los_millis:
            points.append(self._look(tle, frame, t))
            t += step_seconds * 1000
        points.append(self._look(tle, frame, los_millis))
        return points
