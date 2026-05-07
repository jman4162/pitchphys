"""Tests against analytic projectile motion (SPEC §14.1)."""

from __future__ import annotations

import numpy as np

from pitchphys.constants import G_M_S2
from pitchphys.core.environment import Environment
from pitchphys.core.pitch import PitchRelease
from pitchphys.core.simulate import simulate


def test_gravity_only_matches_analytic_projectile() -> None:
    pitch = PitchRelease.from_mph_rpm_axis(
        speed_mph=90.0,
        spin_rpm=0.0,
        tilt_clock=12.0,
        active_spin_fraction=0.0,
        launch_angle_deg=0.0,
        horizontal_angle_deg=0.0,
        release_height_ft=6.0,
        release_side_ft=0.0,
    )
    traj = simulate(pitch, forces=["gravity"], _baselines=False)

    pos0 = pitch.release_pos_m
    v0 = pitch.initial_velocity()
    t = traj.time
    expected_x = pos0[0] + v0[0] * t
    expected_y = pos0[1] + v0[1] * t
    expected_z = pos0[2] + v0[2] * t - 0.5 * G_M_S2 * t * t

    np.testing.assert_allclose(traj.position[:, 0], expected_x, atol=1e-7)
    np.testing.assert_allclose(traj.position[:, 1], expected_y, atol=1e-7)
    np.testing.assert_allclose(traj.position[:, 2], expected_z, atol=1e-6)


def test_no_forces_constant_velocity() -> None:
    pitch = PitchRelease.from_mph_rpm_axis(
        speed_mph=95.0,
        spin_rpm=0.0,
        tilt_clock=12.0,
        active_spin_fraction=0.0,
    )
    traj = simulate(pitch, forces=[], _baselines=False, max_t=0.5)
    v0 = traj.velocity[0]
    for i in range(len(traj.time)):
        np.testing.assert_allclose(traj.velocity[i], v0, atol=1e-9)


def test_gravity_only_no_horizontal_break() -> None:
    pitch = PitchRelease.from_mph_rpm_axis(
        speed_mph=90.0,
        spin_rpm=0.0,
        tilt_clock=12.0,
        active_spin_fraction=0.0,
        launch_angle_deg=0.0,
        horizontal_angle_deg=0.0,
        release_side_ft=0.0,
    )
    traj = simulate(pitch, forces=["gravity"], _baselines=False)
    np.testing.assert_allclose(traj.position[:, 0], 0.0, atol=1e-7)


def test_zero_drag_in_vacuum() -> None:
    """With air_density=0 the drag and Magnus forces vanish."""
    pitch = PitchRelease.from_mph_rpm_axis(speed_mph=95.0, spin_rpm=2400.0, tilt_clock=12.0)
    vacuum = Environment(air_density_kg_m3=0.0)
    traj = simulate(pitch, env=vacuum, forces=["gravity", "drag", "magnus"], _baselines=False)
    # All drag and magnus contributions should be ~0
    np.testing.assert_allclose(traj.forces["drag"], 0.0, atol=1e-12)
    np.testing.assert_allclose(traj.forces["magnus"], 0.0, atol=1e-12)
