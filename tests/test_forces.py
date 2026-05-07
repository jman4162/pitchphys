"""Tests for force decomposition (SPEC §14.1).

Critical sign correctness:
- gravity points only -z
- drag opposes v_rel
- Magnus is +z for backspin, -z for topspin, lateral for sidespin, ~0 for gyro
"""

from __future__ import annotations

import numpy as np
import pytest

from pitchphys.aero import ConstantAeroModel, SimpleMagnusModel
from pitchphys.core.ball import Baseball
from pitchphys.core.environment import Environment
from pitchphys.core.forces import (
    FORCE_REGISTRY,
    drag_force,
    gravity_force,
    magnus_force,
    resolve_forces,
    spin_factor,
)
from pitchphys.core.pitch import PitchRelease


def _state(v: np.ndarray, pos: np.ndarray | None = None) -> np.ndarray:
    if pos is None:
        pos = np.zeros(3)
    return np.concatenate([pos, v])


def _setup() -> tuple[PitchRelease, Environment, Baseball]:
    pitch = PitchRelease.from_mph_rpm_axis(speed_mph=95.0, spin_rpm=2400.0, tilt_clock=12.0)
    return pitch, Environment.sea_level(), Baseball()


def test_gravity_only_z() -> None:
    pitch, env, ball = _setup()
    f = gravity_force(
        0.0,
        _state(np.array([10.0, 30.0, -5.0])),
        pitch,
        env,
        ConstantAeroModel(),
        ball,
        np.zeros(3),
    )
    assert f[0] == 0.0
    assert f[1] == 0.0
    assert f[2] == pytest.approx(-ball.mass_kg * env.gravity_m_s2, rel=1e-12)


def test_drag_opposes_v_rel() -> None:
    pitch, env, ball = _setup()
    v = np.array([3.0, 40.0, -2.0])
    f = drag_force(0.0, _state(v), pitch, env, ConstantAeroModel(), ball, np.zeros(3))
    # Drag dotted with v_rel must be negative.
    assert float(np.dot(f, v)) < 0.0


def test_drag_zero_when_velocity_matches_wind() -> None:
    pitch, _env_zero, ball = _setup()
    env_with_wind = Environment(wind_m_s=np.array([0.0, 40.0, 0.0]))
    v = np.array([0.0, 40.0, 0.0])
    f = drag_force(0.0, _state(v), pitch, env_with_wind, ConstantAeroModel(), ball, np.zeros(3))
    np.testing.assert_allclose(f, np.zeros(3), atol=1e-12)


def test_magnus_backspin_is_upward() -> None:
    pitch, env, ball = _setup()
    omega = np.array([300.0, 0.0, 0.0])  # +x axis = backspin
    v = np.array([0.0, 40.0, 0.0])
    f = magnus_force(0.0, _state(v), pitch, env, SimpleMagnusModel(), ball, omega)
    assert f[2] > 0.0
    assert abs(f[0]) < 1e-9
    assert abs(f[1]) < 1e-9


def test_magnus_topspin_is_downward() -> None:
    pitch, env, ball = _setup()
    omega = np.array([-300.0, 0.0, 0.0])
    v = np.array([0.0, 40.0, 0.0])
    f = magnus_force(0.0, _state(v), pitch, env, SimpleMagnusModel(), ball, omega)
    assert f[2] < 0.0


def test_magnus_3oclock_axis_is_catcher_right() -> None:
    pitch, env, ball = _setup()
    omega = np.array([0.0, 0.0, -300.0])  # 3:00 axis from coordinates convention
    v = np.array([0.0, 40.0, 0.0])
    f = magnus_force(0.0, _state(v), pitch, env, SimpleMagnusModel(), ball, omega)
    assert f[0] > 0.0  # catcher's right
    assert abs(f[2]) < 1e-9


def test_magnus_9oclock_axis_is_catcher_left() -> None:
    pitch, env, ball = _setup()
    omega = np.array([0.0, 0.0, 300.0])
    v = np.array([0.0, 40.0, 0.0])
    f = magnus_force(0.0, _state(v), pitch, env, SimpleMagnusModel(), ball, omega)
    assert f[0] < 0.0


def test_magnus_pure_gyro_is_zero() -> None:
    pitch, env, ball = _setup()
    v = np.array([0.0, 40.0, 0.0])
    omega = np.array([0.0, 300.0, 0.0])  # purely along +y velocity
    f = magnus_force(0.0, _state(v), pitch, env, SimpleMagnusModel(), ball, omega)
    np.testing.assert_allclose(f, np.zeros(3), atol=1e-9)


def test_magnus_zero_when_v_zero() -> None:
    pitch, env, ball = _setup()
    omega = np.array([300.0, 0.0, 0.0])
    f = magnus_force(0.0, _state(np.zeros(3)), pitch, env, SimpleMagnusModel(), ball, omega)
    np.testing.assert_allclose(f, np.zeros(3), atol=1e-12)


def test_spin_factor_zero_when_pure_gyro() -> None:
    omega = np.array([0.0, 200.0, 0.0])
    v_rel = np.array([0.0, 40.0, 0.0])
    assert spin_factor(omega, v_rel, 0.0366) == pytest.approx(0.0, abs=1e-12)


def test_spin_factor_value_for_pure_perp() -> None:
    omega = np.array([200.0, 0.0, 0.0])
    v_rel = np.array([0.0, 40.0, 0.0])
    R = 0.0366
    expected = R * 200.0 / 40.0
    assert spin_factor(omega, v_rel, R) == pytest.approx(expected, rel=1e-12)


def test_resolve_forces_known_names() -> None:
    out = resolve_forces(["gravity", "drag", "magnus"])
    names = [n for n, _ in out]
    assert names == ["gravity", "drag", "magnus"]


def test_resolve_forces_rejects_unknown() -> None:
    with pytest.raises(ValueError):
        resolve_forces(["gravity", "no_such_force"])


def test_force_registry_has_expected_keys() -> None:
    assert {"gravity", "drag", "magnus", "non_magnus"}.issubset(FORCE_REGISTRY.keys())
