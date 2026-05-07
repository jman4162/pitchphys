"""Tests for pure app helpers (cache-key derivation).

No Streamlit imports — these tests run with just the ``[dev]`` extras.
"""

from __future__ import annotations

import numpy as np

from pitchphys._app_helpers import env_to_key, pitch_to_key
from pitchphys.core.environment import Environment
from pitchphys.core.pitch import PitchRelease


def test_pitch_to_key_is_hashable() -> None:
    p = PitchRelease.from_mph_rpm_axis(speed_mph=95.0, spin_rpm=2400.0, tilt_clock=12.0)
    key = pitch_to_key(p)
    cache: dict[object, str] = {}
    cache[key] = "first"
    assert cache[key] == "first"


def test_pitch_to_key_stable_across_construction() -> None:
    a = PitchRelease.from_mph_rpm_axis(speed_mph=95.0, spin_rpm=2400.0, tilt_clock=12.0)
    b = PitchRelease.from_mph_rpm_axis(speed_mph=95.0, spin_rpm=2400.0, tilt_clock=12.0)
    assert pitch_to_key(a) == pitch_to_key(b)


def test_pitch_to_key_changes_with_speed() -> None:
    a = PitchRelease.from_mph_rpm_axis(speed_mph=95.0, spin_rpm=2400.0, tilt_clock=12.0)
    b = PitchRelease.from_mph_rpm_axis(speed_mph=96.0, spin_rpm=2400.0, tilt_clock=12.0)
    assert pitch_to_key(a) != pitch_to_key(b)


def test_pitch_to_key_changes_with_tilt() -> None:
    a = PitchRelease.from_mph_rpm_axis(speed_mph=95.0, spin_rpm=2400.0, tilt_clock=12.0)
    b = PitchRelease.from_mph_rpm_axis(speed_mph=95.0, spin_rpm=2400.0, tilt_clock=11.0)
    assert pitch_to_key(a) != pitch_to_key(b)


def test_env_to_key_distinguishes_sea_level_from_coors() -> None:
    sea = Environment.sea_level()
    coors = Environment.coors_field()
    assert env_to_key(sea) != env_to_key(coors)


def test_env_to_key_distinguishes_wind_vectors() -> None:
    a = Environment(wind_m_s=np.array([0.0, 0.0, 0.0]))
    b = Environment(wind_m_s=np.array([5.0, 0.0, 0.0]))
    assert env_to_key(a) != env_to_key(b)


def test_env_to_key_stable_for_equivalent_envs() -> None:
    a = Environment.sea_level()
    b = Environment.sea_level()
    assert env_to_key(a) == env_to_key(b)


def test_env_to_key_handles_from_weather() -> None:
    e = Environment.from_weather(15.0, 101325.0, 0.5)
    key = env_to_key(e)
    assert isinstance(key, tuple)
    assert all(isinstance(part, (int, float, tuple)) for part in key)
