"""Tests for break metrics."""

from __future__ import annotations

import pytest

from pitchphys.core.environment import Environment
from pitchphys.core.pitch import PitchRelease
from pitchphys.core.simulate import simulate
from pitchphys.metrics import break_metrics


def _backspin_fastball() -> PitchRelease:
    return PitchRelease.from_mph_rpm_axis(speed_mph=95.0, spin_rpm=2400.0, tilt_clock=12.0)


def _topspin_curve() -> PitchRelease:
    return PitchRelease.from_mph_rpm_axis(speed_mph=80.0, spin_rpm=2700.0, tilt_clock=6.0)


def test_release_speed_matches_input() -> None:
    traj = simulate(_backspin_fastball(), _baselines=False)
    assert traj.release_speed_mph == pytest.approx(95.0, rel=1e-9)


def test_plate_speed_less_than_release_with_drag() -> None:
    traj = simulate(_backspin_fastball(), _baselines=False)
    assert traj.plate_speed_mph < traj.release_speed_mph


def test_ivb_positive_for_backspin() -> None:
    traj = simulate(_backspin_fastball())
    assert traj.induced_vertical_break_in > 5.0


def test_ivb_negative_for_topspin() -> None:
    traj = simulate(_topspin_curve())
    assert traj.induced_vertical_break_in < -3.0


def test_total_drop_positive() -> None:
    traj = simulate(_backspin_fastball(), _baselines=False)
    assert traj.total_drop_in > 0.0  # ball ended below release


def test_horizontal_break_near_zero_pure_backspin() -> None:
    traj = simulate(_backspin_fastball())
    # 12:00 backspin produces no horizontal Magnus break.
    assert abs(traj.horizontal_break_in) < 0.5


def test_non_magnus_break_is_zero() -> None:
    traj = simulate(_backspin_fastball())
    assert traj.non_magnus_break_in == 0.0


def test_break_metrics_dict_keys() -> None:
    traj = simulate(_backspin_fastball())
    m = traj.break_metrics()
    assert "release_speed_mph" in m
    assert "induced_vertical_break_in" in m
    assert "magnus_break_x_in" in m
    assert "magnus_break_z_in" in m
    assert "magnus_break_magnitude_in" in m
    assert "non_magnus_break_in" in m


def test_functional_break_metrics_matches_method() -> None:
    traj = simulate(_backspin_fastball())
    assert break_metrics(traj) == traj.break_metrics()


def test_ivb_does_not_require_baseline() -> None:
    """IVB is computed analytically vs a no-force projectile, no baseline needed."""
    traj = simulate(_backspin_fastball(), _baselines=False)
    assert traj.induced_vertical_break_in > 5.0  # backspin still lifts


def test_magnus_break_raises_without_baseline() -> None:
    traj = simulate(_backspin_fastball(), _baselines=False)
    with pytest.raises(ValueError):
        _ = traj.magnus_break_x_in


def test_higher_air_density_more_ivb() -> None:
    pitch = _backspin_fastball()
    sea = simulate(pitch, env=Environment.sea_level())
    coors = simulate(pitch, env=Environment.coors_field())
    # Coors has thinner air -> less Magnus -> less IVB.
    assert coors.induced_vertical_break_in < sea.induced_vertical_break_in


def test_plate_x_z_match_position_endpoint() -> None:
    traj = simulate(_backspin_fastball(), _baselines=False)
    plate_x_ft, plate_z_ft = traj.plate_location()
    assert plate_x_ft == pytest.approx(traj.plate_x_ft)
    assert plate_z_ft == pytest.approx(traj.plate_z_ft)
