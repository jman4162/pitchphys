"""Tests for pitch presets — qualitative behavior only."""

from __future__ import annotations

from pitchphys.core.simulate import simulate
from pitchphys.presets import changeup, curveball, four_seam, sinker, slider


def test_four_seam_release_speed_in_range() -> None:
    traj = simulate(four_seam(speed_mph=95.0))
    assert 90.0 < traj.release_speed_mph < 100.0


def test_four_seam_has_positive_ivb() -> None:
    traj = simulate(four_seam())
    assert traj.induced_vertical_break_in > 5.0


def test_curveball_has_negative_ivb() -> None:
    traj = simulate(curveball())
    assert traj.induced_vertical_break_in < -3.0


def test_gyro_slider_high_spin_low_break() -> None:
    """SPEC §14.2: a high-spin gyro slider should have small total break."""
    traj = simulate(slider(spin_rpm=2500.0, active_spin_fraction=0.30))
    # spin rate is high but total break stays modest
    assert traj.pitch.spin_rate_rad_s > 200.0  # 2500 rpm = 261 rad/s
    total_break_in = (traj.induced_vertical_break_in**2 + traj.horizontal_break_in**2) ** 0.5
    assert total_break_in < 12.0


def test_changeup_slower_than_fastball() -> None:
    fb = simulate(four_seam())
    ch = simulate(changeup())
    assert ch.release_speed_mph < fb.release_speed_mph


def test_sinker_breaks_arm_side_for_rhp() -> None:
    """RHP arm-side = catcher's left = -x."""
    traj = simulate(sinker())
    assert traj.horizontal_break_in < 0.0


def test_changeup_breaks_arm_side_for_rhp() -> None:
    traj = simulate(changeup())
    assert traj.horizontal_break_in < 0.0


def test_sinker_drops_more_than_fastball() -> None:
    fb = simulate(four_seam())
    si = simulate(sinker())
    # Sinker has tilt below 6:00 so Magnus_z is negative.
    assert si.induced_vertical_break_in < fb.induced_vertical_break_in


def test_lefty_four_seam_mirrors_to_eleven_oclock() -> None:
    """LHP four_seam at tilt 1 == RHP at tilt 11 (clock-face mirror)."""
    lhp_at_1 = simulate(four_seam(tilt_clock=1.0, throwing_hand="L"))
    rhp_at_11 = simulate(four_seam(tilt_clock=11.0, throwing_hand="R"))
    assert abs(lhp_at_1.horizontal_break_in - rhp_at_11.horizontal_break_in) < 0.05
    assert abs(lhp_at_1.induced_vertical_break_in - rhp_at_11.induced_vertical_break_in) < 0.05
