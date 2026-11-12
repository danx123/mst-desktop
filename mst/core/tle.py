"""Two-Line Element (TLE) parsing."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from mst.core.constants import DEG_TO_RAD, MU, TWO_PI


@dataclass(frozen=True)
class ParsedTle:
    norad_id: int
    name: str
    epoch_year: int
    epoch_day: float
    epoch_millis: int
    inclination_rad: float
    raan_rad: float
    eccentricity: float
    arg_perigee_rad: float
    mean_anomaly_rad: float
    mean_motion_rev_per_day: float
    mean_motion_rad_per_sec: float
    semi_major_axis_km: float
    bstar: float

    def age_days(self, now_millis: int) -> float:
        return (now_millis - self.epoch_millis) / 86_400_000.0


def _parse_bstar(text: str) -> float:
    try:
        if not text:
            return 0.0
        sign = -1.0 if text.startswith("-") else 1.0
        clean = text.replace("+", "").replace("-", "")
        if len(clean) < 2:
            return 0.0
        mantissa = float("0." + clean[:-2])
        exponent = float(clean[-2:])
        return sign * mantissa * 10.0**exponent
    except ValueError:
        return 0.0


def parse_tle(name: str, line1: str, line2: str) -> Optional[ParsedTle]:
    """Parse a TLE. Returns ``None`` when the lines are malformed."""
    try:
        l1, l2 = line1.strip(), line2.strip()
        if len(l1) < 68 or len(l2) < 68:
            return None

        norad_id = int(l1[2:7])
        short_year = int(l1[18:20])
        epoch_year = 1900 + short_year if short_year >= 57 else 2000 + short_year
        epoch_day = float(l1[20:32])
        jan1 = datetime(epoch_year, 1, 1, tzinfo=timezone.utc)
        epoch_millis = int(jan1.timestamp() * 1000 + (epoch_day - 1.0) * 86_400_000.0)

        bstar = _parse_bstar(l1[53:61].strip())

        inclination = float(l2[8:16])
        raan = float(l2[17:25])
        eccentricity = float("0." + l2[26:33].strip())
        arg_perigee = float(l2[34:42])
        mean_anomaly = float(l2[43:51])
        mean_motion = float(l2[52:63])
        if mean_motion <= 0.0:
            return None

        n_rad_s = mean_motion * TWO_PI / 86_400.0
        semi_major = (MU / (n_rad_s * n_rad_s)) ** (1.0 / 3.0)

        return ParsedTle(
            norad_id=norad_id,
            name=name.strip(),
            epoch_year=epoch_year,
            epoch_day=epoch_day,
            epoch_millis=epoch_millis,
            inclination_rad=inclination * DEG_TO_RAD,
            raan_rad=raan * DEG_TO_RAD,
            eccentricity=eccentricity,
            arg_perigee_rad=arg_perigee * DEG_TO_RAD,
            mean_anomaly_rad=mean_anomaly * DEG_TO_RAD,
            mean_motion_rev_per_day=mean_motion,
            mean_motion_rad_per_sec=n_rad_s,
            semi_major_axis_km=semi_major,
            bstar=bstar,
        )
    except (ValueError, IndexError, ZeroDivisionError):
        return None
