import unittest

from mst.core.models import ObserverLocation
from mst.core.propagator import OrbitPropagator, PropagationError
from mst.core.tle import parse_tle

# Vallado / SGP4 verification set, satellite 00005 (near-Earth).
V5 = (
    "00005",
    "1 00005U 58002B   00179.78495062  .00000023  00000-0  28098-4 0  4753",
    "2 00005  34.2682 348.7242 1859667 331.7664  19.3264 10.82419157413667",
)
GEO = (
    "SATRIA-1",
    "1 57053U 23086A   24001.50000000 -.00000100  00000-0  00000-0 0  9991",
    "2 57053   0.0520  75.4000 0002100 120.4500  45.3000  1.00270000  2105",
)
ISS = (
    "ISS (ZARYA)",
    "1 25544U 98067A   24050.50000000  .00016717  00000-0  10270-3 0  9002",
    "2 25544  51.6400 208.1000 0004800  69.9860  25.0000 15.49815000432101",
)
JAKARTA = ObserverLocation(-6.2088, 106.8456, 10.0, "Jakarta, ID")


def _close(test, got, want, tol):
    for g, w in zip(got, want):
        test.assertAlmostEqual(g, w, delta=tol)


class Sgp4ReferenceTests(unittest.TestCase):
    def setUp(self):
        self.tle = parse_tle(*V5)
        self.prop = OrbitPropagator()

    def test_reference_vector_at_epoch(self):
        r, v = self.prop.propagate_teme(self.tle, self.tle.epoch_millis)
        _close(self, r, (7022.46529266, -1400.08296755, 0.03995155), 0.02)
        _close(self, v, (1.893841015, 6.405893759, 4.534807250), 1e-4)

    def test_reference_vector_after_360_min(self):
        r, v = self.prop.propagate_teme(self.tle, self.tle.epoch_millis + 360 * 60_000)
        _close(self, r, (-7154.03120202, -3783.17682504, -3536.19412294), 0.02)
        _close(self, v, (4.741887409, -4.151817765, -2.093935425), 1e-4)


class ModelSelectionTests(unittest.TestCase):
    def test_model_chosen_from_period(self):
        self.assertFalse(parse_tle(*ISS).is_deep_space)
        self.assertTrue(parse_tle(*GEO).is_deep_space)

    def test_geo_stays_at_geo_altitude(self):
        tle = parse_tle(*GEO)
        for hours in (0, 6, 12, 24, 48):
            pos = OrbitPropagator().position(tle, tle.epoch_millis + hours * 3_600_000, JAKARTA)
            self.assertTrue(35000 < pos.altitude_km < 36500, pos.altitude_km)
            self.assertLess(abs(pos.latitude), 2.0)
            self.assertTrue(2.9 < pos.velocity_km_s < 3.3)

    def test_error_is_reported(self):
        tle = parse_tle(*ISS)
        with self.assertRaises(PropagationError):
            # far enough that drag drives the orbit below the surface
            OrbitPropagator().propagate_teme(tle, tle.epoch_millis + 20_000 * 86_400_000)


if __name__ == "__main__":
    unittest.main()
