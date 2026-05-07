"""Trajectory integrator built on ``scipy.integrate.solve_ivp``.

The plate-crossing event terminates integration at ``y == plate_distance_m``.
Per-step diagnostics (force decomposition, Re, S, Cd, Cl) are filled in via a
second pass over the accepted timesteps so the RHS stays cheap and we don't
need to dedupe rejected steps.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

import numpy as np
from scipy.integrate import solve_ivp

from pitchphys.aero.base import AeroModel, ConstantAeroModel
from pitchphys.aero.lift import NathanLiftModel, SimpleMagnusModel
from pitchphys.aero.lyu import LyuAeroModel
from pitchphys.constants import DEFAULT_PLATE_DISTANCE_M
from pitchphys.core.ball import Baseball
from pitchphys.core.environment import Environment
from pitchphys.core.forces import resolve_forces, reynolds, spin_factor
from pitchphys.core.trajectory import TrajectoryResult

if TYPE_CHECKING:
    from pitchphys.core.pitch import PitchRelease


_DEFAULT_FORCES: tuple[str, ...] = ("gravity", "drag", "magnus")
_MODEL_BY_NAME: dict[str, type[AeroModel]] = {
    "magnus": LyuAeroModel,
    "lyu": LyuAeroModel,
    "simple": SimpleMagnusModel,
    "nathan": NathanLiftModel,
    "constant": ConstantAeroModel,
}


def _resolve_model(model: AeroModel | str) -> AeroModel:
    if isinstance(model, str):
        try:
            return _MODEL_BY_NAME[model]()
        except KeyError as exc:
            raise ValueError(
                f"Unknown aero model {model!r}. Known: {sorted(_MODEL_BY_NAME)}"
            ) from exc
    return model


def simulate(
    pitch: PitchRelease,
    env: Environment | None = None,
    ball: Baseball | None = None,
    model: AeroModel | str = "magnus",
    forces: Sequence[str] | None = None,
    plate_distance_m: float = DEFAULT_PLATE_DISTANCE_M,
    method: Literal["RK45", "DOP853"] = "RK45",
    rtol: float = 1e-8,
    atol: float = 1e-10,
    max_t: float = 2.0,
    spin_decay_tau_s: float | None = 1.5,
    _baselines: bool = True,
) -> TrajectoryResult:
    """Integrate a pitch from release to plate.

    Args:
        pitch: Initial conditions.
        env: Atmospheric environment (defaults to sea level).
        ball: Baseball physical properties (defaults to standard).
        model: Either a string name (``"magnus"``, ``"lyu"``, ``"simple"``,
            ``"nathan"``, ``"constant"``) or an AeroModel instance.
        forces: Force names to include (e.g. ``["gravity", "drag", "magnus"]``).
            Defaults to all three. An empty list is allowed (free flight).
        plate_distance_m: Y-coordinate where the integration terminates.
        method: ``"RK45"`` (default) or ``"DOP853"``.
        rtol, atol: Solver tolerances.
        max_t: Maximum integration time in seconds.
        spin_decay_tau_s: Exponential time constant for spin decay,
            ``omega(t) = omega_0 * exp(-t / tau)``. Default ``1.5 s`` is an
            Adair-baseline value that gives ~23 % decay over a 0.4 s flight.
            Pass ``None`` to disable decay (omega stays constant; matches
            SPEC §8.1 strict reading and Nathan 2008's fit assumption).
        _baselines: Internal. If True and ``"magnus"`` is in ``forces``, also
            simulate a gravity+drag baseline for Magnus-break diagnostics.

    Returns:
        ``TrajectoryResult`` with arrays sampled at the integrator's accepted
        timesteps and break-metric properties available.
    """
    env = env or Environment.sea_level()
    ball = ball or Baseball()
    model = _resolve_model(model)
    force_names = tuple(_DEFAULT_FORCES if forces is None else forces)
    resolved = resolve_forces(force_names)

    v0 = pitch.initial_velocity()
    y0 = np.concatenate([pitch.release_pos_m, v0])
    omega_0 = pitch.omega_vec(v0 / max(float(np.linalg.norm(v0)), 1e-12))

    def omega_at(t: float) -> np.ndarray:
        if spin_decay_tau_s is None:
            return omega_0
        return omega_0 * math.exp(-t / spin_decay_tau_s)

    def rhs(t: float, y: np.ndarray) -> np.ndarray:
        omega = omega_at(t)
        F = np.zeros(3)
        for _, f in resolved:
            F = F + f(t, y, pitch, env, model, ball, omega)
        a = F / ball.mass_kg
        return np.concatenate([y[3:6], a])

    def plate_event(t: float, y: np.ndarray) -> float:
        return float(y[1] - plate_distance_m)

    plate_event.terminal = True  # type: ignore[attr-defined]
    plate_event.direction = 1.0  # type: ignore[attr-defined]

    sol = solve_ivp(
        rhs,
        (0.0, max_t),
        y0,
        method=method,
        events=plate_event,
        rtol=rtol,
        atol=atol,
        dense_output=False,
    )
    if not sol.success:
        raise RuntimeError(f"solve_ivp failed: {sol.message}")

    t_arr = sol.t
    y_arr = sol.y.T  # (N, 6)
    pos = y_arr[:, :3]
    vel = y_arr[:, 3:]
    n = len(t_arr)

    # Second pass: compute per-step force decomposition + aero diagnostics.
    forces_per_step: dict[str, np.ndarray] = {name: np.zeros((n, 3)) for name, _ in resolved}
    accel = np.zeros((n, 3))
    Re_arr = np.zeros(n)
    S_arr = np.zeros(n)
    Cd_arr = np.zeros(n)
    Cl_arr = np.zeros(n)
    for i in range(n):
        t_i = float(t_arr[i])
        y_i = y_arr[i]
        omega_i = omega_at(t_i)
        F_total = np.zeros(3)
        for name, f in resolved:
            F_i = f(t_i, y_i, pitch, env, model, ball, omega_i)
            forces_per_step[name][i] = F_i
            F_total = F_total + F_i
        accel[i] = F_total / ball.mass_kg
        v_i = y_i[3:6] - env.wind_m_s
        speed = float(np.linalg.norm(v_i))
        if speed > 1e-12:
            Re_arr[i] = reynolds(speed, ball, env)
            S_arr[i] = spin_factor(omega_i, v_i, ball.radius_m)
            Cd_arr[i] = float(model.cd(Re_arr[i], S_arr[i], {}))
            Cl_arr[i] = float(model.cl(Re_arr[i], S_arr[i], {}))

    # Magnus break needs a gravity+drag baseline (same physics minus Magnus).
    grav_drag_baseline: TrajectoryResult | None = None
    if (
        _baselines
        and "magnus" in force_names
        and "drag" in force_names
        and "gravity" in force_names
    ):
        gd_forces = [n for n in force_names if n in ("gravity", "drag")]
        try:
            grav_drag_baseline = simulate(
                pitch,
                env=env,
                ball=ball,
                model=model,
                forces=gd_forces,
                plate_distance_m=plate_distance_m,
                method=method,
                rtol=rtol,
                atol=atol,
                max_t=max_t,
                spin_decay_tau_s=spin_decay_tau_s,
                _baselines=False,
            )
        except RuntimeError:
            grav_drag_baseline = None

    return TrajectoryResult(
        time=t_arr,
        position=pos,
        velocity=vel,
        acceleration=accel,
        forces=forces_per_step,
        reynolds_number=Re_arr,
        spin_factor=S_arr,
        cd=Cd_arr,
        cl=Cl_arr,
        plate_distance_m=plate_distance_m,
        ball=ball,
        env=env,
        pitch=pitch,
        forces_used=force_names,
        grav_drag_baseline=grav_drag_baseline,
        metadata={"method": method, "rtol": rtol, "atol": atol},
    )


def simulate_many(
    pitches: Sequence[PitchRelease],
    **kwargs: object,
) -> list[TrajectoryResult]:
    """Run :func:`simulate` over a sequence of pitches (sequential in v0.1)."""
    return [simulate(p, **kwargs) for p in pitches]  # type: ignore[arg-type]
