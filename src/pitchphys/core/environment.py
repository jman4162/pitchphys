"""Atmospheric and gravitational environment (SPEC §9.2)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from pitchphys.constants import (
    AIR_DENSITY_SEA_LEVEL,
    DYNAMIC_VISCOSITY_SEA_LEVEL,
    G_M_S2,
)

# Specific gas constants used in the humid-air calculation in from_weather.
_R_DRY_AIR = 287.058  # J / (kg * K)
_R_WATER_VAPOR = 461.495  # J / (kg * K)
# Sutherland's law constants for air viscosity.
_SUTHERLAND_REF_VISCOSITY = 1.716e-5  # Pa * s at T_ref
_SUTHERLAND_T_REF_K = 273.15
_SUTHERLAND_S_K = 110.4


def _zero_wind() -> np.ndarray:
    return np.zeros(3)


@dataclass(frozen=True, slots=True)
class Environment:
    """Air properties, gravity, and wind.

    Wind is a 3-vector in world frame (m/s). Drag uses ``v_rel = v - wind``.
    """

    air_density_kg_m3: float = AIR_DENSITY_SEA_LEVEL
    dynamic_viscosity_pa_s: float = DYNAMIC_VISCOSITY_SEA_LEVEL
    gravity_m_s2: float = G_M_S2
    wind_m_s: np.ndarray = field(default_factory=_zero_wind)

    @classmethod
    def sea_level(cls) -> Environment:
        """Standard sea-level air at 15 deg C."""
        return cls()

    @classmethod
    def coors_field(cls) -> Environment:
        """Approximate Denver / Coors Field air density (~5,200 ft elevation).

        The 1.00 kg/m^3 value is approximate; real conditions vary with
        temperature and humidity. Use :meth:`from_weather` for explicit
        sensitivity studies.
        """
        return cls(air_density_kg_m3=1.00)

    @classmethod
    def from_weather(
        cls,
        temp_c: float,
        pressure_pa: float,
        humidity: float = 0.0,
    ) -> Environment:
        """Air properties from temperature, pressure, and relative humidity.

        Uses the ideal-gas law with the Tetens equation for water-vapor
        saturation pressure and a humid-air partial-pressure mixture. Dynamic
        viscosity is computed via Sutherland's law.

        Args:
            temp_c: Air temperature in degrees Celsius.
            pressure_pa: Total atmospheric pressure in Pa
                (sea-level standard ≈ 101325).
            humidity: Relative humidity in ``[0, 1]``. ``0`` for dry air.

        Returns:
            ``Environment`` with computed ``air_density_kg_m3`` and
            ``dynamic_viscosity_pa_s``. ``gravity_m_s2`` and ``wind_m_s``
            keep their defaults.

        Note:
            Humid air is *less* dense than dry air at the same pressure
            because water vapor (M ≈ 18 g/mol) is lighter than the
            nitrogen/oxygen mix (M ≈ 29 g/mol). At 30 °C, 100 % RH,
            sea-level pressure, this is ~1 % less dense than dry air.
        """
        if not 0.0 <= humidity <= 1.0:
            raise ValueError(f"humidity must be in [0, 1], got {humidity!r}")
        if pressure_pa <= 0:
            raise ValueError(f"pressure_pa must be positive, got {pressure_pa!r}")

        t_kelvin = temp_c + 273.15
        # Tetens equation: saturation vapor pressure of water (Pa).
        p_sat = 610.78 * math.exp(17.27 * temp_c / (temp_c + 237.3))
        p_vapor = humidity * p_sat
        p_dry = pressure_pa - p_vapor
        rho = p_dry / (_R_DRY_AIR * t_kelvin) + p_vapor / (_R_WATER_VAPOR * t_kelvin)

        # Sutherland's law for dynamic viscosity of air.
        mu = (
            _SUTHERLAND_REF_VISCOSITY
            * (t_kelvin / _SUTHERLAND_T_REF_K) ** 1.5
            * (_SUTHERLAND_T_REF_K + _SUTHERLAND_S_K)
            / (t_kelvin + _SUTHERLAND_S_K)
        )
        return cls(air_density_kg_m3=rho, dynamic_viscosity_pa_s=mu)
