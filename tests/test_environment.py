"""Tests for Environment.from_weather and Sutherland viscosity."""

from __future__ import annotations

import pytest

from pitchphys.core.environment import Environment


def test_from_weather_15c_sea_level_matches_default() -> None:
    """ISA standard at 15 °C, 101325 Pa, 0 % humidity ≈ default sea-level."""
    env = Environment.from_weather(15.0, 101325.0, 0.0)
    default = Environment.sea_level()
    # The from_weather model gives ~1.225 kg/m³ (within ~0.5%).
    assert env.air_density_kg_m3 == pytest.approx(default.air_density_kg_m3, rel=0.005)


def test_from_weather_higher_temp_lower_density() -> None:
    cold = Environment.from_weather(0.0, 101325.0, 0.0)
    hot = Environment.from_weather(40.0, 101325.0, 0.0)
    assert hot.air_density_kg_m3 < cold.air_density_kg_m3


def test_from_weather_lower_pressure_lower_density() -> None:
    sea = Environment.from_weather(15.0, 101325.0, 0.0)
    coors = Environment.from_weather(15.0, 83000.0, 0.0)  # ~5,200 ft
    assert coors.air_density_kg_m3 < sea.air_density_kg_m3
    # Coors should land near 1.00 ± 0.05
    assert 0.95 < coors.air_density_kg_m3 < 1.05


def test_from_weather_humid_air_less_dense() -> None:
    """Counterintuitive but correct: humid air is less dense than dry air."""
    dry = Environment.from_weather(30.0, 101325.0, 0.0)
    humid = Environment.from_weather(30.0, 101325.0, 1.0)
    assert humid.air_density_kg_m3 < dry.air_density_kg_m3
    # At 30 °C, 100 % RH the density drop is ~1 %.
    assert (dry.air_density_kg_m3 - humid.air_density_kg_m3) / dry.air_density_kg_m3 < 0.02


def test_from_weather_viscosity_at_15c() -> None:
    """Sutherland viscosity at 15 °C ≈ 1.79e-5 Pa·s.

    The often-cited "sea-level standard" value 1.81e-5 corresponds to ~25 °C;
    Sutherland's law gives 1.79e-5 at 15 °C.
    """
    env = Environment.from_weather(15.0, 101325.0, 0.0)
    assert env.dynamic_viscosity_pa_s == pytest.approx(1.79e-5, rel=0.02)


def test_from_weather_viscosity_higher_at_warmer_temp() -> None:
    cold = Environment.from_weather(0.0, 101325.0, 0.0)
    hot = Environment.from_weather(40.0, 101325.0, 0.0)
    assert hot.dynamic_viscosity_pa_s > cold.dynamic_viscosity_pa_s


def test_from_weather_rejects_invalid_humidity() -> None:
    with pytest.raises(ValueError):
        Environment.from_weather(15.0, 101325.0, -0.1)
    with pytest.raises(ValueError):
        Environment.from_weather(15.0, 101325.0, 1.5)


def test_from_weather_rejects_invalid_pressure() -> None:
    with pytest.raises(ValueError):
        Environment.from_weather(15.0, 0.0, 0.0)
    with pytest.raises(ValueError):
        Environment.from_weather(15.0, -100.0, 0.0)
