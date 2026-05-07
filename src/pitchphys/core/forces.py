"""Force callables (gravity, drag, Magnus) and the registry that maps names
to callables.

All force functions share the same signature so the integrator can sum them
agnostically:

    f(t, state, pitch, env, model, ball, omega) -> np.ndarray  # shape (3,)

``state`` is the full ODE state ``[x, y, z, vx, vy, vz]``. ``omega`` is the
angular velocity vector held constant for the integration (SPEC §8.1).
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TYPE_CHECKING

import numpy as np

from pitchphys.coordinates import decompose_omega

if TYPE_CHECKING:
    from pitchphys.aero.base import AeroModel
    from pitchphys.core.ball import Baseball
    from pitchphys.core.environment import Environment
    from pitchphys.core.pitch import PitchRelease


ForceFn = Callable[
    [
        float,
        np.ndarray,
        "PitchRelease",
        "Environment",
        "AeroModel",
        "Baseball",
        np.ndarray,
    ],
    np.ndarray,
]


_EPS = 1e-12


def reynolds(speed: float, ball: Baseball, env: Environment) -> float:
    """Reynolds number for a sphere of diameter ``2 * ball.radius_m`` in air."""
    return env.air_density_kg_m3 * speed * (2.0 * ball.radius_m) / env.dynamic_viscosity_pa_s


def spin_factor(omega: np.ndarray, v_rel: np.ndarray, radius_m: float) -> float:
    """Dimensionless spin factor ``S = R * |omega_perp| / |v_rel|`` (SPEC §4.3)."""
    speed = float(np.linalg.norm(v_rel))
    if speed < _EPS:
        return 0.0
    v_hat = v_rel / speed
    perp, _ = decompose_omega(omega, v_hat)
    return radius_m * float(np.linalg.norm(perp)) / speed


def gravity_force(
    t: float,
    state: np.ndarray,
    pitch: PitchRelease,
    env: Environment,
    model: AeroModel,
    ball: Baseball,
    omega: np.ndarray,
) -> np.ndarray:
    return np.array([0.0, 0.0, -ball.mass_kg * env.gravity_m_s2])


def drag_force(
    t: float,
    state: np.ndarray,
    pitch: PitchRelease,
    env: Environment,
    model: AeroModel,
    ball: Baseball,
    omega: np.ndarray,
) -> np.ndarray:
    v = state[3:6]
    v_rel = v - env.wind_m_s
    speed = float(np.linalg.norm(v_rel))
    if speed < _EPS:
        return np.zeros(3)
    Re = reynolds(speed, ball, env)
    S = spin_factor(omega, v_rel, ball.radius_m)
    Cd = float(model.cd(Re, S, {}))
    out = -0.5 * env.air_density_kg_m3 * Cd * ball.area_m2 * speed * v_rel
    return np.asarray(out, dtype=float)


def magnus_force(
    t: float,
    state: np.ndarray,
    pitch: PitchRelease,
    env: Environment,
    model: AeroModel,
    ball: Baseball,
    omega: np.ndarray,
) -> np.ndarray:
    v = state[3:6]
    v_rel = v - env.wind_m_s
    speed = float(np.linalg.norm(v_rel))
    if speed < _EPS:
        return np.zeros(3)
    v_hat = v_rel / speed
    perp, _ = decompose_omega(omega, v_hat)
    perp_mag = float(np.linalg.norm(perp))
    if perp_mag < _EPS:
        return np.zeros(3)
    Re = reynolds(speed, ball, env)
    S = ball.radius_m * perp_mag / speed
    Cl = float(model.cl(Re, S, {}))
    cross = np.cross(omega, v_rel)
    cross_mag = float(np.linalg.norm(cross))
    if cross_mag < _EPS:
        return np.zeros(3)
    direction = cross / cross_mag
    return 0.5 * env.air_density_kg_m3 * Cl * ball.area_m2 * speed * speed * direction


def non_magnus_force(
    t: float,
    state: np.ndarray,
    pitch: PitchRelease,
    env: Environment,
    model: AeroModel,
    ball: Baseball,
    omega: np.ndarray,
) -> np.ndarray:
    """Delegates to ``model.non_magnus_force``. v0.1 built-ins return zero."""
    return np.asarray(model.non_magnus_force(t, state, pitch, env), dtype=float)


FORCE_REGISTRY: dict[str, ForceFn] = {
    "gravity": gravity_force,
    "drag": drag_force,
    "magnus": magnus_force,
    "non_magnus": non_magnus_force,
}


def resolve_forces(names: Sequence[str]) -> list[tuple[str, ForceFn]]:
    """Look up force callables by name, preserving order. Raises on unknowns."""
    out: list[tuple[str, ForceFn]] = []
    for name in names:
        if name not in FORCE_REGISTRY:
            raise ValueError(f"Unknown force {name!r}. Known forces: {sorted(FORCE_REGISTRY)}")
        out.append((name, FORCE_REGISTRY[name]))
    return out
