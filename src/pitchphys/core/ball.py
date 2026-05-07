"""Baseball physical properties (SPEC §9.1)."""

from __future__ import annotations

import math
from dataclasses import dataclass

from pitchphys.constants import BASEBALL_MASS_KG, BASEBALL_RADIUS_M


@dataclass(frozen=True, slots=True)
class Baseball:
    """A point-mass baseball.

    Defaults are MLB rule midpoints (mass 5.0-5.25 oz, circumference
    9.0-9.25 in). Override for different ball lots, training balls, etc.
    """

    mass_kg: float = BASEBALL_MASS_KG
    radius_m: float = BASEBALL_RADIUS_M
    seam_height_m: float | None = None

    @property
    def area_m2(self) -> float:
        """Cross-sectional area used in drag/lift formulas."""
        return math.pi * self.radius_m * self.radius_m

    @property
    def diameter_m(self) -> float:
        return 2.0 * self.radius_m
