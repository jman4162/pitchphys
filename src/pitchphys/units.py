"""SI unit conversion helpers.

The simulation core stores meters, seconds, kilograms, radians. These helpers
convert at the user-facing boundary so mph/rpm/feet/inches never leak into
force calculations.
"""

from __future__ import annotations

import math
from typing import TypeVar

import numpy as np

# Accept floats and numpy arrays; preserve type via TypeVar.
Numeric = TypeVar("Numeric", float, np.floating, np.ndarray)

_MPH_TO_MPS = 0.44704
_FT_TO_M = 0.3048
_IN_TO_M = 0.0254
_RPM_TO_RADPS = 2.0 * math.pi / 60.0


def mph_to_mps(mph: Numeric) -> Numeric:
    return mph * _MPH_TO_MPS


def mps_to_mph(mps: Numeric) -> Numeric:
    return mps / _MPH_TO_MPS


def rpm_to_radps(rpm: Numeric) -> Numeric:
    return rpm * _RPM_TO_RADPS


def radps_to_rpm(radps: Numeric) -> Numeric:
    return radps / _RPM_TO_RADPS


def ft_to_m(ft: Numeric) -> Numeric:
    return ft * _FT_TO_M


def m_to_ft(m: Numeric) -> Numeric:
    return m / _FT_TO_M


def in_to_m(inches: Numeric) -> Numeric:
    return inches * _IN_TO_M


def m_to_in(m: Numeric) -> Numeric:
    return m / _IN_TO_M
