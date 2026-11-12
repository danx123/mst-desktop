"""Physical and mathematical constants (WGS-84 / EGM)."""
import math

EARTH_RADIUS_KM = 6378.137
EARTH_FLATTENING = 1.0 / 298.257223563
EARTH_E2 = 2 * EARTH_FLATTENING - EARTH_FLATTENING * EARTH_FLATTENING
MU = 398600.4418  # km^3 / s^2
J2 = 1.08262668e-3
OMEGA_E = 7.2921151467e-5  # rad / s

TWO_PI = 2.0 * math.pi
DEG_TO_RAD = math.pi / 180.0
RAD_TO_DEG = 180.0 / math.pi
