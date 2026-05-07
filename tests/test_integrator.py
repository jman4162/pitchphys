"""Tests for plate-event termination and integrator stability."""

from __future__ import annotations

import pytest

from pitchphys.constants import DEFAULT_PLATE_DISTANCE_M
from pitchphys.core.pitch import PitchRelease
from pitchphys.core.simulate import simulate


def _fastball() -> PitchRelease:
    return PitchRelease.from_mph_rpm_axis(speed_mph=95.0, spin_rpm=2400.0, tilt_clock=12.0)


def test_plate_event_terminates_at_correct_y() -> None:
    traj = simulate(_fastball(), _baselines=False)
    assert traj.position[-1, 1] == pytest.approx(DEFAULT_PLATE_DISTANCE_M, abs=1e-6)


def test_plate_position_stable_across_tolerances() -> None:
    loose = simulate(_fastball(), rtol=1e-6, atol=1e-8, _baselines=False)
    tight = simulate(_fastball(), rtol=1e-10, atol=1e-12, _baselines=False)
    # 0.05 inch = 0.00127 m
    assert abs(loose.position[-1, 0] - tight.position[-1, 0]) < 0.00127
    assert abs(loose.position[-1, 2] - tight.position[-1, 2]) < 0.00127


def test_rk45_and_dop853_agree() -> None:
    rk = simulate(_fastball(), method="RK45", _baselines=False)
    dop = simulate(_fastball(), method="DOP853", _baselines=False)
    # 0.01 inch = 0.000254 m
    assert abs(rk.position[-1, 0] - dop.position[-1, 0]) < 0.000254
    assert abs(rk.position[-1, 2] - dop.position[-1, 2]) < 0.000254


def test_simulate_with_unknown_force_raises() -> None:
    with pytest.raises(ValueError):
        simulate(_fastball(), forces=["gravity", "weird"], _baselines=False)


def test_simulate_with_unknown_model_raises() -> None:
    with pytest.raises(ValueError):
        simulate(_fastball(), model="not_a_model", _baselines=False)


def test_simulate_returns_diagnostics() -> None:
    traj = simulate(_fastball(), _baselines=False)
    n = len(traj.time)
    assert traj.position.shape == (n, 3)
    assert traj.velocity.shape == (n, 3)
    assert traj.acceleration.shape == (n, 3)
    assert traj.forces["gravity"].shape == (n, 3)
    assert traj.forces["drag"].shape == (n, 3)
    assert traj.forces["magnus"].shape == (n, 3)
    assert traj.cd.shape == (n,)
    assert traj.cl.shape == (n,)
