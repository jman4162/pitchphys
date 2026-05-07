"""Cross-cutting qualitative tests (SPEC §14.2)."""

from __future__ import annotations

import itertools
import math

from pitchphys.core.environment import Environment
from pitchphys.core.pitch import PitchRelease
from pitchphys.core.simulate import simulate


def test_same_speed_spin_different_axis_different_break() -> None:
    """Same speed/spin but different tilts produce different break directions."""
    a = simulate(
        PitchRelease.from_mph_rpm_axis(
            speed_mph=88.0,
            spin_rpm=2200.0,
            tilt_clock=12.0,
            active_spin_fraction=0.95,
        )
    )
    b = simulate(
        PitchRelease.from_mph_rpm_axis(
            speed_mph=88.0,
            spin_rpm=2200.0,
            tilt_clock=9.0,
            active_spin_fraction=0.95,
        )
    )
    # angle between break vectors must exceed 30 degrees
    va = (a.horizontal_break_in, a.induced_vertical_break_in)
    vb = (b.horizontal_break_in, b.induced_vertical_break_in)
    norm_a = math.hypot(*va)
    norm_b = math.hypot(*vb)
    cos_angle = (va[0] * vb[0] + va[1] * vb[1]) / (norm_a * norm_b)
    angle_deg = math.degrees(math.acos(max(-1.0, min(1.0, cos_angle))))
    assert angle_deg > 30.0


def test_higher_active_spin_more_movement() -> None:
    """|IVB| grows monotonically with active_spin_fraction (backspin pitch)."""
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
        assert curr >= prev - 1e-6


def test_coors_field_less_magnus_break_than_sea_level() -> None:
    """Lower air density -> smaller Magnus break."""
    pitch = PitchRelease.from_mph_rpm_axis(
        speed_mph=95.0,
        spin_rpm=2400.0,
        tilt_clock=12.0,
        active_spin_fraction=0.95,
    )
    sea = simulate(pitch, env=Environment.sea_level())
    coors = simulate(pitch, env=Environment.coors_field())
    assert coors.magnus_break_z_in < sea.magnus_break_z_in


def test_higher_spin_rate_more_movement_at_fixed_axis() -> None:
    """At fixed tilt and active fraction, more spin -> more break."""
    breaks: list[float] = []
    for rpm in (1500.0, 2000.0, 2500.0, 3000.0):
        traj = simulate(
            PitchRelease.from_mph_rpm_axis(
                speed_mph=92.0,
                spin_rpm=rpm,
                tilt_clock=12.0,
                active_spin_fraction=0.95,
            )
        )
        breaks.append(traj.induced_vertical_break_in)
    for prev, curr in itertools.pairwise(breaks):
        assert curr > prev


def test_drag_brings_pitch_in_higher_air_density_more_decel() -> None:
    """Sea-level pitch loses more speed than Coors-field pitch."""
    pitch = PitchRelease.from_mph_rpm_axis(
        speed_mph=95.0, spin_rpm=0.0, tilt_clock=12.0, active_spin_fraction=0.0
    )
    sea = simulate(pitch, env=Environment.sea_level())
    coors = simulate(pitch, env=Environment.coors_field())
    sea_loss = sea.release_speed_mph - sea.plate_speed_mph
    coors_loss = coors.release_speed_mph - coors.plate_speed_mph
    assert sea_loss > coors_loss
