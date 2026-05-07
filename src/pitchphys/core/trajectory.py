"""TrajectoryResult: storage + lazy break-metric properties (SPEC §11)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

from pitchphys.units import m_to_ft, m_to_in, mps_to_mph

if TYPE_CHECKING:
    from pitchphys.core.ball import Baseball
    from pitchphys.core.environment import Environment
    from pitchphys.core.pitch import PitchRelease


@dataclass(frozen=True)
class TrajectoryResult:
    """Sampled trajectory + per-step diagnostics.

    Arrays are indexed along axis 0 by accepted-integrator timesteps. Forces
    are stored per name in the ``forces`` dict (each value shape ``(N, 3)``).

    Break metrics rely on baseline trajectories simulated with subsets of the
    forces: ``gravity_only_baseline`` (forces=["gravity"]) drives induced
    vertical break; ``grav_drag_baseline`` (forces=["gravity","drag"]) drives
    Magnus break.
    """

    time: np.ndarray
    position: np.ndarray  # (N, 3)
    velocity: np.ndarray  # (N, 3)
    acceleration: np.ndarray  # (N, 3)
    forces: dict[str, np.ndarray]  # name -> (N, 3)
    reynolds_number: np.ndarray  # (N,)
    spin_factor: np.ndarray  # (N,)
    cd: np.ndarray  # (N,)
    cl: np.ndarray  # (N,)
    plate_distance_m: float
    ball: Baseball
    env: Environment
    pitch: PitchRelease
    forces_used: tuple[str, ...]
    grav_drag_baseline: TrajectoryResult | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    # ----- core metrics -----

    @property
    def flight_time_s(self) -> float:
        return float(self.time[-1])

    @property
    def plate_x_ft(self) -> float:
        return float(m_to_ft(self.position[-1, 0]))

    @property
    def plate_z_ft(self) -> float:
        return float(m_to_ft(self.position[-1, 2]))

    def plate_location(self) -> tuple[float, float]:
        """``(plate_x_ft, plate_z_ft)`` at the moment of plate crossing."""
        return self.plate_x_ft, self.plate_z_ft

    @property
    def release_speed_mph(self) -> float:
        return float(mps_to_mph(np.linalg.norm(self.velocity[0])))

    @property
    def plate_speed_mph(self) -> float:
        return float(mps_to_mph(np.linalg.norm(self.velocity[-1])))

    # ----- break metrics -----

    @property
    def total_drop_in(self) -> float:
        """Inches the ball ended below the release height (positive = below)."""
        return float(m_to_in(self.position[0, 2] - self.position[-1, 2]))

    @property
    def horizontal_break_in(self) -> float:
        """Lateral deviation from a straight-line projection of the release velocity.

        Positive = catcher's right.
        """
        flight = self.flight_time_s
        x_no_force = float(self.position[0, 0] + self.velocity[0, 0] * flight)
        return float(m_to_in(self.position[-1, 0] - x_no_force))

    @property
    def induced_vertical_break_in(self) -> float:
        """Vertical movement induced by aerodynamic forces (Statcast §4.1).

        Defined as the difference in ``z`` between the actual pitch and a
        no-force projectile with the same release velocity, evaluated at the
        actual pitch's flight time:

            z_no_force(t) = z0 + vz0 * t - 0.5 * g * t**2

        Positive ⇒ the ball ended above the gravity-only path (the pitch
        "rises" relative to a spinless ball). Negative ⇒ extra drop. For a
        pure-gyro pitch with no Magnus contribution to z, IVB ≈ 0 by
        construction.
        """
        t = self.flight_time_s
        z0 = float(self.position[0, 2])
        vz0 = float(self.velocity[0, 2])
        g = self.env.gravity_m_s2
        z_no_force = z0 + vz0 * t - 0.5 * g * t * t
        return float(m_to_in(self.position[-1, 2] - z_no_force))

    @property
    def magnus_break_x_in(self) -> float:
        """X component of break vs. a gravity+drag baseline."""
        if self.grav_drag_baseline is None:
            raise ValueError("magnus_break_* requires the gravity+drag baseline.")
        return float(m_to_in(self.position[-1, 0] - self.grav_drag_baseline.position[-1, 0]))

    @property
    def magnus_break_z_in(self) -> float:
        if self.grav_drag_baseline is None:
            raise ValueError("magnus_break_* requires the gravity+drag baseline.")
        return float(m_to_in(self.position[-1, 2] - self.grav_drag_baseline.position[-1, 2]))

    @property
    def magnus_break_magnitude_in(self) -> float:
        return float(np.hypot(self.magnus_break_x_in, self.magnus_break_z_in))

    @property
    def non_magnus_break_in(self) -> float:
        """Reserved for v0.3 seam-shifted-wake models. Always 0.0 in v0.1."""
        return 0.0

    def break_metrics(self) -> dict[str, float]:
        """Return all break metrics as a dictionary."""
        out: dict[str, float] = {
            "release_speed_mph": self.release_speed_mph,
            "plate_speed_mph": self.plate_speed_mph,
            "flight_time_s": self.flight_time_s,
            "plate_x_ft": self.plate_x_ft,
            "plate_z_ft": self.plate_z_ft,
            "total_drop_in": self.total_drop_in,
            "horizontal_break_in": self.horizontal_break_in,
            "induced_vertical_break_in": self.induced_vertical_break_in,
            "non_magnus_break_in": self.non_magnus_break_in,
        }
        if self.grav_drag_baseline is not None:
            out["magnus_break_x_in"] = self.magnus_break_x_in
            out["magnus_break_z_in"] = self.magnus_break_z_in
            out["magnus_break_magnitude_in"] = self.magnus_break_magnitude_in
        return out
