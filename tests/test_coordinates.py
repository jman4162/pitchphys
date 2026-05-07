"""Tests for spin-axis convention and decomposition."""

from __future__ import annotations

import numpy as np
import pytest

from pitchphys.coordinates import build_omega, clock_tilt_to_axis, decompose_omega


def test_clock_12_is_pure_backspin_axis() -> None:
    axis = clock_tilt_to_axis(12.0)  # 12:00 wraps to 0
    np.testing.assert_allclose(axis, [1.0, 0.0, 0.0], atol=1e-12)


def test_clock_0_equivalent_to_12() -> None:
    np.testing.assert_allclose(clock_tilt_to_axis(0.0), clock_tilt_to_axis(12.0), atol=1e-12)


def test_clock_6_is_pure_topspin_axis() -> None:
    np.testing.assert_allclose(clock_tilt_to_axis(6.0), [-1.0, 0.0, 0.0], atol=1e-12)


def test_clock_3_axis_is_minus_z() -> None:
    np.testing.assert_allclose(clock_tilt_to_axis(3.0), [0.0, 0.0, -1.0], atol=1e-12)


def test_clock_9_axis_is_plus_z() -> None:
    np.testing.assert_allclose(clock_tilt_to_axis(9.0), [0.0, 0.0, 1.0], atol=1e-12)


def test_clock_axis_is_unit() -> None:
    for c in (0.0, 1.5, 2.7, 4.0, 7.25, 11.99):
        np.testing.assert_allclose(np.linalg.norm(clock_tilt_to_axis(c)), 1.0, atol=1e-12)


def test_lefty_mirrors_input_clock() -> None:
    """LHP at tilt T == RHP at tilt (12 - T): mirror the clock face."""
    np.testing.assert_allclose(
        clock_tilt_to_axis(1.0, "L"), clock_tilt_to_axis(11.0, "R"), atol=1e-12
    )
    np.testing.assert_allclose(
        clock_tilt_to_axis(3.0, "L"), clock_tilt_to_axis(9.0, "R"), atol=1e-12
    )


def test_lefty_12_6_axes_invariant() -> None:
    """12:00 and 6:00 are on the mirror axis itself; no change."""
    np.testing.assert_allclose(
        clock_tilt_to_axis(12.0, "L"), clock_tilt_to_axis(12.0, "R"), atol=1e-12
    )
    np.testing.assert_allclose(
        clock_tilt_to_axis(6.0, "L"), clock_tilt_to_axis(6.0, "R"), atol=1e-12
    )


def test_decompose_omega_orthogonality() -> None:
    rng = np.random.default_rng(42)
    for _ in range(10):
        omega = rng.normal(size=3)
        v = rng.normal(size=3)
        v_hat = v / np.linalg.norm(v)
        perp, par = decompose_omega(omega, v_hat)
        # perp is orthogonal to v_hat; par is parallel
        assert abs(np.dot(perp, v_hat)) < 1e-12
        np.testing.assert_allclose(np.cross(par, v_hat), np.zeros(3), atol=1e-12)


def test_decompose_omega_recombines() -> None:
    rng = np.random.default_rng(7)
    omega = rng.normal(size=3)
    v_hat = np.array([0.05, 0.99, -0.02])
    perp, par = decompose_omega(omega, v_hat)
    np.testing.assert_allclose(perp + par, omega, atol=1e-12)


def test_build_omega_pure_active_yields_axis_aligned_with_active() -> None:
    v_hat = np.array([0.0, 1.0, 0.0])
    active_axis = np.array([1.0, 0.0, 0.0])
    omega = build_omega(100.0, active_axis, active_spin_fraction=1.0, v_hat=v_hat)
    np.testing.assert_allclose(omega, [100.0, 0.0, 0.0], atol=1e-12)


def test_build_omega_pure_gyro_along_velocity() -> None:
    v_hat = np.array([0.0, 1.0, 0.0])
    active_axis = np.array([1.0, 0.0, 0.0])
    omega = build_omega(50.0, active_axis, active_spin_fraction=0.0, v_hat=v_hat)
    np.testing.assert_allclose(omega, [0.0, 50.0, 0.0], atol=1e-12)


def test_build_omega_active_fraction_matches_decomposition() -> None:
    v_hat = np.array([0.0, 1.0, 0.0])
    active_axis = np.array([1.0, 0.0, 0.0])
    spin = 200.0
    for a in (0.0, 0.25, 0.5, 0.75, 0.95, 1.0):
        omega = build_omega(spin, active_axis, active_spin_fraction=a, v_hat=v_hat)
        perp, _ = decompose_omega(omega, v_hat)
        ratio = np.linalg.norm(perp) / np.linalg.norm(omega)
        assert ratio == pytest.approx(a, abs=1e-12)


def test_build_omega_rejects_out_of_range_fraction() -> None:
    with pytest.raises(ValueError):
        build_omega(
            100.0,
            np.array([1.0, 0.0, 0.0]),
            active_spin_fraction=1.5,
            v_hat=np.array([0.0, 1.0, 0.0]),
        )
