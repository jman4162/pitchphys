"""Tests for the spin-decay parameter on simulate()."""

from __future__ import annotations

import math

import numpy as np
import pytest

from pitchphys.core.pitch import PitchRelease
from pitchphys.core.simulate import simulate


def _high_spin_fastball() -> PitchRelease:
    return PitchRelease.from_mph_rpm_axis(
        speed_mph=95.0, spin_rpm=2400.0, tilt_clock=12.0, active_spin_fraction=0.95
    )


def test_no_decay_keeps_omega_constant() -> None:
    """With ``spin_decay_tau_s=None`` the spin factor at the plate matches release."""
    traj = simulate(_high_spin_fastball(), spin_decay_tau_s=None)
    s_release = traj.spin_factor[0]
    s_plate = traj.spin_factor[-1]
    # Spin factor S = R*|omega_perp|/|v|. Drag slows |v|, so S grows even at
    # constant omega — we only assert that *omega* is constant by checking
    # that S * v == constant within numerical tolerance.
    R = traj.ball.radius_m
    v_release = float(np.linalg.norm(traj.velocity[0]))
    v_plate = float(np.linalg.norm(traj.velocity[-1]))
    omega_perp_release = s_release * v_release / R
    omega_perp_plate = s_plate * v_plate / R
    assert omega_perp_plate == pytest.approx(omega_perp_release, rel=1e-3)


def test_decay_reduces_omega_at_plate() -> None:
    """With finite tau the effective omega_perp decreases over the flight."""
    traj = simulate(_high_spin_fastball(), spin_decay_tau_s=1.5)
    R = traj.ball.radius_m
    v_release = float(np.linalg.norm(traj.velocity[0]))
    v_plate = float(np.linalg.norm(traj.velocity[-1]))
    omega_perp_release = traj.spin_factor[0] * v_release / R
    omega_perp_plate = traj.spin_factor[-1] * v_plate / R
    assert omega_perp_plate < omega_perp_release


def test_decay_matches_analytic_at_plate_time() -> None:
    """The omega-decay schedule is exact: omega(t) = omega(0)*exp(-t/tau)."""
    tau = 1.5
    traj = simulate(_high_spin_fastball(), spin_decay_tau_s=tau)
    R = traj.ball.radius_m
    t_plate = traj.flight_time_s
    v_plate = float(np.linalg.norm(traj.velocity[-1]))
    v_release = float(np.linalg.norm(traj.velocity[0]))
    omega_perp_release = traj.spin_factor[0] * v_release / R
    omega_perp_plate = traj.spin_factor[-1] * v_plate / R
    expected_ratio = math.exp(-t_plate / tau)
    actual_ratio = omega_perp_plate / omega_perp_release
    # Tolerance limited by integrator + small v_hat rotation between release
    # and plate (gravity tilts v_hat by ~1 deg over a fastball flight).
    assert actual_ratio == pytest.approx(expected_ratio, rel=2e-3)


def test_short_tau_collapses_ivb() -> None:
    """With tau much smaller than flight time, IVB approaches gravity-only (~0)."""
    no_decay = simulate(_high_spin_fastball(), spin_decay_tau_s=None)
    rapid_decay = simulate(_high_spin_fastball(), spin_decay_tau_s=0.05)
    # Spin essentially zero by mid-flight => Magnus break collapses
    assert abs(rapid_decay.induced_vertical_break_in) < 0.5 * abs(
        no_decay.induced_vertical_break_in
    )


def test_decay_preserves_ivb_sign_for_backspin() -> None:
    """A backspin pitch with decay still has positive IVB (sign unchanged)."""
    traj = simulate(_high_spin_fastball(), spin_decay_tau_s=1.5)
    assert traj.induced_vertical_break_in > 0.0


def test_decay_makes_ivb_smaller_than_no_decay_for_backspin() -> None:
    no_decay = simulate(_high_spin_fastball(), spin_decay_tau_s=None)
    decay = simulate(_high_spin_fastball(), spin_decay_tau_s=1.5)
    assert decay.induced_vertical_break_in < no_decay.induced_vertical_break_in


def test_decay_for_pure_topspin_is_smaller_drop() -> None:
    """A topspin pitch with decay drops less than without decay."""
    pitch = PitchRelease.from_mph_rpm_axis(
        speed_mph=80.0,
        spin_rpm=2700.0,
        tilt_clock=6.0,
        active_spin_fraction=0.85,
    )
    no_decay = simulate(pitch, spin_decay_tau_s=None)
    decay = simulate(pitch, spin_decay_tau_s=1.5)
    # Both negative; decayed has smaller magnitude
    assert no_decay.induced_vertical_break_in < 0.0
    assert decay.induced_vertical_break_in < 0.0
    assert abs(decay.induced_vertical_break_in) < abs(no_decay.induced_vertical_break_in)


def test_decay_baseline_uses_same_tau() -> None:
    """The grav+drag baseline used for magnus_break inherits the same tau."""
    traj = simulate(_high_spin_fastball(), spin_decay_tau_s=1.5)
    assert traj.grav_drag_baseline is not None
    # Baseline has no Magnus contribution but should still use spin decay
    # for diagnostic consistency. Check spin_factor decays in baseline too.
    R = traj.ball.radius_m
    bl = traj.grav_drag_baseline
    v_release = float(np.linalg.norm(bl.velocity[0]))
    v_plate = float(np.linalg.norm(bl.velocity[-1]))
    omega_perp_release = bl.spin_factor[0] * v_release / R
    omega_perp_plate = bl.spin_factor[-1] * v_plate / R
    assert omega_perp_plate < omega_perp_release
