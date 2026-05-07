"""Tests for Baseball, Environment, and PitchRelease."""

from __future__ import annotations

import math

import numpy as np
import pytest

from pitchphys.coordinates import decompose_omega
from pitchphys.core.ball import Baseball
from pitchphys.core.environment import Environment
from pitchphys.core.pitch import PitchRelease


def test_baseball_default_area() -> None:
    b = Baseball()
    assert b.area_m2 == pytest.approx(math.pi * 0.0366 * 0.0366, rel=1e-12)


def test_baseball_diameter() -> None:
    assert Baseball().diameter_m == pytest.approx(2 * 0.0366, rel=1e-12)


def test_baseball_is_frozen() -> None:
    b = Baseball()
    with pytest.raises(Exception):
        b.mass_kg = 0.2  # type: ignore[misc]


def test_environment_sea_level() -> None:
    env = Environment.sea_level()
    assert env.air_density_kg_m3 == pytest.approx(1.225, rel=1e-12)
    assert env.gravity_m_s2 == pytest.approx(9.80665, rel=1e-12)
    np.testing.assert_allclose(env.wind_m_s, [0.0, 0.0, 0.0])


def test_environment_coors_field_is_thinner() -> None:
    assert Environment.coors_field().air_density_kg_m3 < Environment.sea_level().air_density_kg_m3


def test_pitch_from_mph_rpm_axis_units() -> None:
    p = PitchRelease.from_mph_rpm_axis(speed_mph=95.0, spin_rpm=2400.0, tilt_clock=12.0)
    assert p.speed_m_s == pytest.approx(95.0 * 0.44704, rel=1e-12)
    assert p.spin_rate_rad_s == pytest.approx(2400.0 * 2 * math.pi / 60.0, rel=1e-12)


def test_pitch_release_position_meters() -> None:
    p = PitchRelease.from_mph_rpm_axis(
        speed_mph=90.0,
        spin_rpm=2200.0,
        tilt_clock=12.0,
        release_height_ft=6.0,
        release_side_ft=-1.5,
    )
    np.testing.assert_allclose(p.release_pos_m, [-1.5 * 0.3048, 0.0, 6.0 * 0.3048], atol=1e-12)


def test_pitch_initial_velocity_mostly_y() -> None:
    p = PitchRelease.from_mph_rpm_axis(
        speed_mph=95.0,
        spin_rpm=2400.0,
        tilt_clock=12.0,
        launch_angle_deg=-1.0,
        horizontal_angle_deg=0.0,
    )
    v = p.initial_velocity()
    speed = float(np.linalg.norm(v))
    assert speed == pytest.approx(p.speed_m_s, rel=1e-12)
    assert v[1] > 0.99 * speed  # mostly forward


def test_pitch_active_spin_fraction_split() -> None:
    p = PitchRelease.from_mph_rpm_axis(
        speed_mph=85.0,
        spin_rpm=2500.0,
        tilt_clock=12.0,
        active_spin_fraction=0.5,
    )
    v = p.initial_velocity()
    v_hat = v / np.linalg.norm(v)
    omega = p.omega_vec(v_hat)
    perp, _ = decompose_omega(omega, v_hat)
    ratio = float(np.linalg.norm(perp) / np.linalg.norm(omega))
    assert ratio == pytest.approx(0.5, abs=1e-9)


def test_pitch_pure_backspin_axis_is_plus_x() -> None:
    p = PitchRelease.from_mph_rpm_axis(
        speed_mph=95.0,
        spin_rpm=2400.0,
        tilt_clock=12.0,
        active_spin_fraction=1.0,
        launch_angle_deg=0.0,
        horizontal_angle_deg=0.0,
    )
    np.testing.assert_allclose(p.spin_axis, [1.0, 0.0, 0.0], atol=1e-12)


def test_pitch_pure_topspin_axis_is_minus_x() -> None:
    p = PitchRelease.from_mph_rpm_axis(
        speed_mph=80.0,
        spin_rpm=2700.0,
        tilt_clock=6.0,
        active_spin_fraction=1.0,
        launch_angle_deg=0.0,
        horizontal_angle_deg=0.0,
    )
    np.testing.assert_allclose(p.spin_axis, [-1.0, 0.0, 0.0], atol=1e-12)
