"""Physical constants used throughout pitchphys.

All values are SI. Baseball mass and radius are midpoints of MLB rules
(weight 5.0-5.25 oz, circumference 9.0-9.25 in).
"""

from __future__ import annotations

from pitchphys.units import ft_to_m

G_M_S2: float = 9.80665
"""Standard gravity (m/s^2)."""

BASEBALL_MASS_KG: float = 0.145
"""Default baseball mass (kg). MLB rule midpoint of 5.0-5.25 oz."""

BASEBALL_RADIUS_M: float = 0.0366
"""Default baseball radius (m). MLB rule midpoint of 9.0-9.25 in circumference."""

AIR_DENSITY_SEA_LEVEL: float = 1.225
"""Sea-level standard-atmosphere air density (kg/m^3)."""

DYNAMIC_VISCOSITY_SEA_LEVEL: float = 1.81e-5
"""Sea-level dry-air dynamic viscosity (Pa*s)."""

DEFAULT_PLATE_DISTANCE_M: float = ft_to_m(55.0)
"""Default release-to-plate distance (m). 55 ft mirrors typical pitcher
extension off a 60.5 ft rubber-to-plate distance."""
