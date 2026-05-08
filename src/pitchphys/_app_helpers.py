"""Streamlit-app helpers that don't require Streamlit at import time.

These live inside the installed package (rather than under ``app/``) so
tests can import them without setting up Streamlit. The widget code in
``app/utils.py`` calls into these for cache-key derivation, strike-zone
classification, trajectory CSV serialization, and URL state encoding.
"""

from __future__ import annotations

import io
from typing import TYPE_CHECKING

import numpy as np

from pitchphys.coordinates import (
    STRIKE_ZONE_BOTTOM_FT,
    STRIKE_ZONE_HALF_WIDTH_FT,
    STRIKE_ZONE_TOP_FT,
)

if TYPE_CHECKING:
    from pitchphys.core.environment import Environment
    from pitchphys.core.pitch import PitchRelease
    from pitchphys.core.trajectory import TrajectoryResult


# ---------------------------------------------------------------------------
# Cache keys
# ---------------------------------------------------------------------------


def pitch_to_key(p: PitchRelease) -> tuple[object, ...]:
    """Hashable tuple representation of a PitchRelease for caching."""
    return (
        round(p.speed_m_s, 6),
        round(p.launch_angle_deg, 6),
        round(p.horizontal_angle_deg, 6),
        tuple(round(float(v), 6) for v in p.release_pos_m),
        round(p.spin_rate_rad_s, 6),
        tuple(round(float(v), 6) for v in p.spin_axis),
        round(p.active_spin_fraction, 6),
    )


def env_to_key(e: Environment) -> tuple[object, ...]:
    """Hashable tuple representation of an Environment for caching."""
    return (
        round(e.air_density_kg_m3, 6),
        round(e.dynamic_viscosity_pa_s, 9),
        round(e.gravity_m_s2, 6),
        tuple(round(float(v), 6) for v in e.wind_m_s),
    )


# ---------------------------------------------------------------------------
# Strike zone classification
# ---------------------------------------------------------------------------


def is_strike(plate_x_ft: float, plate_z_ft: float) -> bool:
    """Return True if the pitch crosses the rule-book strike zone.

    Uses the half-plate-width (8.5 in) plus the canonical zone heights
    from :mod:`pitchphys.coordinates`. The sign convention matches
    ``TrajectoryResult.plate_x_ft`` (positive = catcher's right).
    """
    return (
        abs(plate_x_ft) < STRIKE_ZONE_HALF_WIDTH_FT
        and STRIKE_ZONE_BOTTOM_FT < plate_z_ft < STRIKE_ZONE_TOP_FT
    )


# ---------------------------------------------------------------------------
# Trajectory CSV serialization
# ---------------------------------------------------------------------------


def trajectory_to_csv(traj: TrajectoryResult) -> str:
    """Serialize a TrajectoryResult to a CSV string suitable for download.

    Columns: ``t_s, x_m, y_m, z_m, vx_m_s, vy_m_s, vz_m_s, F_grav_N,
    F_drag_N, F_magnus_N``. Force columns are magnitudes (N) per timestep;
    forces not present in the simulation are written as ``nan``.
    """
    n = len(traj.time)
    rows = np.zeros((n, 10))
    rows[:, 0] = traj.time
    rows[:, 1:4] = traj.position
    rows[:, 4:7] = traj.velocity
    for col, fname in enumerate(("gravity", "drag", "magnus"), start=7):
        if fname in traj.forces:
            rows[:, col] = np.linalg.norm(traj.forces[fname], axis=1)
        else:
            rows[:, col] = np.nan

    header = "t_s,x_m,y_m,z_m,vx_m_s,vy_m_s,vz_m_s,F_grav_N,F_drag_N,F_magnus_N"
    buf = io.StringIO()
    np.savetxt(buf, rows, delimiter=",", header=header, comments="", fmt="%.6g")
    return buf.getvalue()


# ---------------------------------------------------------------------------
# URL state encoding (Streamlit query params)
# ---------------------------------------------------------------------------


CANONICAL_PITCH_KEYS: tuple[str, ...] = (
    "speed_mph",
    "spin_rpm",
    "tilt_clock",
    "active_spin_fraction",
    "release_height_ft",
    "release_side_ft",
    "throwing_hand",
)


def pack_url_params(canonical: dict[str, object]) -> dict[str, str]:
    """Convert a canonical-pitch dict into stringly-typed URL query params.

    Floats use 6-significant-digit formatting; other types are stringified.
    Only keys in :data:`CANONICAL_PITCH_KEYS` are encoded.
    """
    out: dict[str, str] = {}
    for key in CANONICAL_PITCH_KEYS:
        if key not in canonical:
            continue
        value = canonical[key]
        if isinstance(value, float):
            out[key] = f"{value:.6g}"
        else:
            out[key] = str(value)
    return out


def unpack_url_params(params: dict[str, str]) -> dict[str, object]:
    """Parse string URL query params back into a canonical-pitch dict.

    Floats are cast for all keys except ``throwing_hand`` (which stays a
    string). Unknown keys are dropped. Invalid values for known keys are
    silently dropped (keep the user's session-state default in those
    cases).
    """
    out: dict[str, object] = {}
    for key in CANONICAL_PITCH_KEYS:
        if key not in params:
            continue
        raw = params[key]
        if key == "throwing_hand":
            if raw.upper() in ("R", "L"):
                out[key] = raw.upper()
            continue
        try:
            out[key] = float(raw)
        except (TypeError, ValueError):
            continue
    return out
