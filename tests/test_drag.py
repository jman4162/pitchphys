"""Tests for drag deceleration and air-density sensitivity."""

from __future__ import annotations

import numpy as np

from pitchphys.core.environment import Environment
from pitchphys.core.pitch import PitchRelease
from pitchphys.core.simulate import simulate


def _spinless(speed_mph: float = 95.0) -> PitchRelease:
    return PitchRelease.from_mph_rpm_axis(
        speed_mph=speed_mph,
        spin_rpm=0.0,
        tilt_clock=12.0,
        active_spin_fraction=0.0,
    )


def test_drag_decelerates_pitch() -> None:
    pitch = _spinless()
    traj = simulate(pitch, forces=["gravity", "drag"], _baselines=False)
    assert float(np.linalg.norm(traj.velocity[-1])) < float(np.linalg.norm(traj.velocity[0]))


def test_thinner_air_means_less_drag() -> None:
    pitch = _spinless()
    sea = simulate(pitch, env=Environment.sea_level(), forces=["gravity", "drag"], _baselines=False)
    coors = simulate(
        pitch, env=Environment.coors_field(), forces=["gravity", "drag"], _baselines=False
    )
    assert coors.plate_speed_mph > sea.plate_speed_mph


def test_drag_dotted_with_velocity_negative() -> None:
    pitch = _spinless()
    traj = simulate(pitch, forces=["gravity", "drag"], _baselines=False)
    # Inspect a few mid-flight indices.
    for i in range(0, len(traj.time), max(1, len(traj.time) // 5)):
        v_rel = traj.velocity[i] - traj.env.wind_m_s
        f_drag = traj.forces["drag"][i]
        if float(np.linalg.norm(v_rel)) > 1e-6:
            assert float(np.dot(f_drag, v_rel)) < 0.0
