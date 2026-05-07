"""End-to-end Magnus / spin tests on simulated trajectories."""

from __future__ import annotations

import itertools

from pitchphys.core.pitch import PitchRelease
from pitchphys.core.simulate import simulate


def _spinless_fastball() -> PitchRelease:
    return PitchRelease.from_mph_rpm_axis(
        speed_mph=95.0,
        spin_rpm=0.0,
        tilt_clock=12.0,
        active_spin_fraction=0.0,
    )


def _high_active_fastball() -> PitchRelease:
    return PitchRelease.from_mph_rpm_axis(
        speed_mph=95.0,
        spin_rpm=2400.0,
        tilt_clock=12.0,
        active_spin_fraction=0.95,
    )


def _gyro_only_fastball() -> PitchRelease:
    return PitchRelease.from_mph_rpm_axis(
        speed_mph=95.0,
        spin_rpm=2400.0,
        tilt_clock=12.0,
        active_spin_fraction=0.0,
    )


def test_backspin_lifts_relative_to_no_force_projectile() -> None:
    fast = simulate(_high_active_fastball())
    assert fast.induced_vertical_break_in > 0.0


def test_topspin_drops_more_than_no_force_projectile() -> None:
    curve = simulate(
        PitchRelease.from_mph_rpm_axis(
            speed_mph=80.0,
            spin_rpm=2700.0,
            tilt_clock=6.0,
            active_spin_fraction=0.95,
        )
    )
    assert curve.induced_vertical_break_in < 0.0


def test_pure_gyro_pitch_low_break_relative_to_active() -> None:
    """A pure-gyro pitch produces only small Magnus break.

    Some coupling occurs because gravity tilts ``v_hat`` mid-flight, so
    ``omega`` (held constant) is no longer aligned with velocity and a small
    perpendicular component appears. Compare instead to a high-active pitch
    with the same total spin: the gyro pitch has |IVB| at most ~25% of the
    high-active version.
    """
    gyro = simulate(_gyro_only_fastball())
    active = simulate(_high_active_fastball())
    assert abs(gyro.induced_vertical_break_in) < 0.25 * active.induced_vertical_break_in
    assert abs(gyro.horizontal_break_in) < 0.25 * abs(active.induced_vertical_break_in)


def test_active_spin_fraction_monotone_ivb() -> None:
    ivbs: list[float] = []
    for a in (0.0, 0.25, 0.5, 0.75, 0.95):
        traj = simulate(
            PitchRelease.from_mph_rpm_axis(
                speed_mph=95.0,
                spin_rpm=2400.0,
                tilt_clock=12.0,
                active_spin_fraction=a,
            )
        )
        ivbs.append(traj.induced_vertical_break_in)
    for prev, curr in itertools.pairwise(ivbs):
        assert curr >= prev - 1e-6  # monotonically non-decreasing


def test_horizontal_break_3oclock_positive() -> None:
    """3:00 axis (-z) yields +x Magnus break (catcher's right)."""
    p = PitchRelease.from_mph_rpm_axis(
        speed_mph=88.0,
        spin_rpm=2200.0,
        tilt_clock=3.0,
        active_spin_fraction=0.95,
    )
    traj = simulate(p)
    assert traj.horizontal_break_in > 5.0  # noticeable rightward break


def test_horizontal_break_9oclock_negative() -> None:
    p = PitchRelease.from_mph_rpm_axis(
        speed_mph=88.0,
        spin_rpm=2200.0,
        tilt_clock=9.0,
        active_spin_fraction=0.95,
    )
    traj = simulate(p)
    assert traj.horizontal_break_in < -5.0


def test_spinless_fastball_drops_more_than_high_spin_fastball() -> None:
    spinless = simulate(_spinless_fastball())
    high = simulate(_high_active_fastball())
    assert spinless.total_drop_in > high.total_drop_in
