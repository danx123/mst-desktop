"""CelesTrak GP API client (TLE format)."""
from __future__ import annotations

import time
import urllib.error
import urllib.request

from mst.i18n import tr
from mst.core.models import Satellite

BASE_URL = "https://celestrak.org/NORAD/elements/gp.php"
USER_AGENT = "MST-MacanSatelliteTracker/1.0 (Desktop)"

# (CelesTrak group, local category, i18n key of the menu label)
SYNC_GROUPS: list[tuple[str, str, str]] = [
    ("stations", "STATIONS", "sync.stations"),
    ("weather", "WEATHER", "sync.weather"),
    ("starlink", "STARLINK", "sync.starlink"),
    ("geo", "GEO", "sync.geo"),
]


class CelesTrakError(Exception):
    pass


def parse_tle_response(raw_text: str, category: str) -> list[Satellite]:
    lines = [ln.strip() for ln in raw_text.splitlines() if ln.strip()]
    now = int(time.time() * 1000)
    result: list[Satellite] = []

    i = 0
    while i + 2 < len(lines):
        name, line1, line2 = lines[i], lines[i + 1], lines[i + 2]
        if (
            line1.startswith("1 ")
            and line2.startswith("2 ")
            and len(line1) >= 68
            and len(line2) >= 68
        ):
            try:
                norad_id = int(line1[2:7])
            except ValueError:
                i += 1
                continue
            result.append(Satellite(norad_id, name, line1, line2, category, False, now))
            i += 3
            continue
        i += 1
    return result


def fetch_group(group: str, category: str, timeout: float = 15.0) -> list[Satellite]:
    url = f"{BASE_URL}?GROUP={group}&FORMAT=tle"
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        raise CelesTrakError(tr("err.http", code=exc.code, reason=exc.reason)) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise CelesTrakError(str(getattr(exc, "reason", exc)) or tr("err.connection")) from exc

    satellites = parse_tle_response(body, category)
    if not satellites:
        snippet = body.strip().splitlines()[0][:120] if body.strip() else tr("err.empty")
        raise CelesTrakError(tr("err.no_tle", snippet=snippet))
    return satellites
