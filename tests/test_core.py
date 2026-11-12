import tempfile
import unittest
from pathlib import Path

from mst.core.models import ObserverLocation, Satellite
from mst.core.passes import PassPredictor
from mst.core.propagator import OrbitPropagator
from mst.core.tle import parse_tle
from mst.data.celestrak import parse_tle_response
from mst.data.database import SatelliteDatabase
from mst.data.default_satellites import default_satellites
from mst.data.repository import SatelliteRepository

ISS = (
    "ISS (ZARYA)",
    "1 25544U 98067A   24050.50000000  .00016717  00000-0  10270-3 0  9002",
    "2 25544  51.6400 208.1000 0004800  69.9860  25.0000 15.49815000432101",
)
SATRIA = (
    "SATRIA-1",
    "1 57053U 23086A   24001.50000000 -.00000100  00000-0  00000-0 0  9991",
    "2 57053   0.0520  75.4000 0002100 120.4500  45.3000  1.00270000  2105",
)
JAKARTA = ObserverLocation(-6.2088, 106.8456, 10.0, "Jakarta, ID")
T0 = 1710000000000


class TleTests(unittest.TestCase):
    def test_parse_iss(self):
        tle = parse_tle(*ISS)
        self.assertIsNotNone(tle)
        self.assertEqual(tle.norad_id, 25544)
        self.assertEqual(tle.epoch_year, 2024)
        self.assertAlmostEqual(tle.age_days(T0), 19.0, delta=1.0)

    def test_parse_rejects_garbage(self):
        self.assertIsNone(parse_tle("X", "1 bad", "2 bad"))

    def test_all_defaults_parse(self):
        for sat in default_satellites():
            self.assertIsNotNone(parse_tle(sat.name, sat.line1, sat.line2), sat.name)

    def test_geo_period(self):
        tle = parse_tle(*SATRIA)
        self.assertTrue(1400.0 < 1440.0 / tle.mean_motion_rev_per_day < 1450.0)


class PropagatorTests(unittest.TestCase):
    def test_iss_position_sane(self):
        tle = parse_tle(*ISS)
        pos = OrbitPropagator().position(tle, T0, JAKARTA)
        self.assertGreater(pos.altitude_km, 300)
        self.assertTrue(6.0 < pos.velocity_km_s < 9.0)
        self.assertTrue(80 < pos.period_minutes < 110)
        self.assertTrue(0 <= pos.azimuth_deg <= 360)
        self.assertTrue(-90 <= pos.elevation_deg <= 90)
        self.assertLessEqual(abs(pos.latitude), 51.7)

    def test_ground_track_length(self):
        tle = parse_tle(*ISS)
        track = OrbitPropagator().ground_track(tle, T0, 90, 60)
        self.assertEqual(len(track), 91)

    def test_passes_are_ordered_and_valid(self):
        tle = parse_tle(*ISS)
        passes = PassPredictor().predict(tle, JAKARTA, T0, 48, 10.0)
        self.assertGreater(len(passes), 0)
        last = 0
        for p in passes:
            self.assertLess(p.aos_time_millis, p.max_elevation_time_millis + 1)
            self.assertLessEqual(p.max_elevation_time_millis, p.los_time_millis)
            self.assertGreaterEqual(p.max_elevation_deg, 10.0)
            self.assertGreater(p.duration_seconds, 60)
            self.assertGreater(p.aos_time_millis, last)
            last = p.los_time_millis

    def test_pass_path(self):
        tle = parse_tle(*ISS)
        p = PassPredictor().predict(tle, JAKARTA, T0, 48, 10.0)[0]
        path = PassPredictor().pass_path(tle, JAKARTA, p.aos_time_millis, p.los_time_millis)
        self.assertGreater(len(path), 5)
        self.assertGreater(max(el for _, el in path), 9.0)


class DataTests(unittest.TestCase):
    def setUp(self):
        self._dir = tempfile.TemporaryDirectory()
        self.db = SatelliteDatabase(Path(self._dir.name) / "t.db")

    def tearDown(self):
        self.db.close()
        self._dir.cleanup()

    def test_seed_and_favorites(self):
        repo = SatelliteRepository(self.db)
        repo.seed_defaults_if_empty()
        repo.seed_defaults_if_empty()  # idempotent
        self.assertEqual(len(repo.all()), 15)
        repo.toggle_favorite(41999)
        self.assertTrue(self.db.get(41999).is_favorite)

    def test_sync_keeps_favorites_and_indonesia_category(self):
        def fake_fetch(group, category):
            now = 1
            return [
                Satellite(41999, "TELKOM 3S", "1 x" + "0" * 70, "2 x" + "0" * 70, category, False, now),
                Satellite(99999, "NEW SAT", "1 x" + "0" * 70, "2 x" + "0" * 70, category, False, now),
            ]

        repo = SatelliteRepository(self.db, fetch=fake_fetch)
        repo.seed_defaults_if_empty()
        repo.toggle_favorite(41999)
        self.assertEqual(repo.sync_from_celestrak("geo", "GEO"), 2)
        sat = self.db.get(41999)
        self.assertTrue(sat.is_favorite)
        self.assertEqual(sat.category, "INDONESIA")
        self.assertEqual(self.db.get(99999).category, "GEO")

    def test_parse_celestrak_text(self):
        raw = "\n".join(ISS) + "\n" + "\n".join(SATRIA) + "\n"
        sats = parse_tle_response(raw, "STATIONS")
        self.assertEqual([s.norad_id for s in sats], [25544, 57053])


if __name__ == "__main__":
    unittest.main()
