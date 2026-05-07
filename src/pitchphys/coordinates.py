"""Coordinate system and spin-axis convention.

This module is the **single source of truth** for how clock-face spin tilts
map to 3D spin-axis vectors. Every other module that needs to interpret a
spin axis should call into this module rather than re-deriving the rotation.

World axes (right-handed):
    x = horizontal, positive to catcher's right
    y = forward, positive from release toward home plate
    z = vertical, positive up

Spin tilt is described as a clock face viewed from behind home plate looking
toward the pitcher (catcher view). For a right-handed pitcher (RHP):

        12 (backspin)
         |
   9 ----+---- 3
         |
         6 (topspin)

    12:00 -> axis = +x  (pure backspin -> +z Magnus break, "lift")
     3:00 -> axis = -z  (sidespin     -> +x Magnus break, catcher's right)
     6:00 -> axis = -x  (pure topspin -> -z Magnus break, "drop")
     9:00 -> axis = +z  (sidespin     -> -x Magnus break, catcher's left)

The mapping of tilt T (in clock hours) to the 3D axis is a planar rotation
in the catcher-view (x, z) plane:

    angle_rad = -pi * T / 6           # measured clockwise from 12:00
    axis      = (cos(angle_rad), 0, sin(angle_rad))

For an LHP, the resulting axis is mirrored across the 12-6 axis (x -> -x).

Magnus force is always proportional to ``omega x v_hat``, so under v_hat = +y
the break direction equals the clock-tilt direction itself: 12:00 break = up,
6:00 break = down, 3:00 break = catcher's right, 9:00 break = catcher's left.
This is intentional (the convention is internally consistent) and is the
mental model users should keep.
"""

from __future__ import annotations

import math
from typing import Literal

import numpy as np

# Strike zone (rough constants for visualization; not used in physics).
STRIKE_ZONE_TOP_FT: float = 3.5
STRIKE_ZONE_BOTTOM_FT: float = 1.5
STRIKE_ZONE_HALF_WIDTH_FT: float = 8.5 / 12.0  # half of a 17-inch plate


def clock_tilt_to_axis(
    tilt_clock_hours: float,
    throwing_hand: Literal["R", "L"] = "R",
) -> np.ndarray:
    """Map a clock-face tilt to a 3D unit vector along the active spin axis.

    Args:
        tilt_clock_hours: Clock tilt in hours, ``0`` <= tilt < ``12``.
            Fractional values are allowed (e.g. ``1.5`` for 1:30). Out-of-range
            inputs are reduced modulo 12.
        throwing_hand: ``"R"`` (default) or ``"L"``. For ``"L"`` the resulting
            axis is mirrored across the 12-6 axis by flipping ``x``.

    Returns:
        Unit 3-vector ``(x, y, z)`` lying in the catcher-view (x, z) plane.
    """
    c = float(tilt_clock_hours) % 12.0
    if throwing_hand.upper() == "L":
        c = (12.0 - c) % 12.0  # mirror across the 12-6 axis on the clock face
    angle_rad = -math.pi * c / 6.0  # clockwise from 12 in catcher view
    axis = np.array([math.cos(angle_rad), 0.0, math.sin(angle_rad)])
    # Numerical hygiene: re-normalize (cos/sin can drift by ~1e-17).
    return np.asarray(axis / np.linalg.norm(axis), dtype=float)


def build_omega(
    spin_rate_rad_s: float,
    active_axis: np.ndarray,
    active_spin_fraction: float,
    v_hat: np.ndarray,
) -> np.ndarray:
    """Compose the full 3D angular velocity vector from an active axis + gyro mix.

    ``active_spin_fraction`` is the share of the spin that is perpendicular to
    velocity (and therefore contributes to the Magnus force, SPEC §4.4). The
    remaining share is gyro spin aligned with velocity:

        omega = spin_rate * (active_spin_fraction * active_axis_hat
                             + gyro_fraction * v_hat)

    where ``gyro_fraction = sqrt(1 - active_spin_fraction^2)``.

    Args:
        spin_rate_rad_s: Spin magnitude in rad/s.
        active_axis: 3-vector along the active (perpendicular) spin axis.
            Need not be a unit vector; it will be normalized.
        active_spin_fraction: In ``[0, 1]``. ``1.0`` means pure active spin.
        v_hat: Unit velocity direction at release.

    Returns:
        3-vector angular velocity in rad/s.
    """
    if not 0.0 <= active_spin_fraction <= 1.0:
        raise ValueError(f"active_spin_fraction must be in [0, 1], got {active_spin_fraction!r}")
    gyro_fraction = math.sqrt(max(0.0, 1.0 - active_spin_fraction**2))
    a_hat = active_axis / np.linalg.norm(active_axis)
    v_hat_norm = v_hat / np.linalg.norm(v_hat)
    out = spin_rate_rad_s * (active_spin_fraction * a_hat + gyro_fraction * v_hat_norm)
    return np.asarray(out, dtype=float)


def decompose_omega(
    omega: np.ndarray,
    v_hat: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    """Split angular velocity into perpendicular and parallel components.

    ``omega = omega_perp + omega_par`` where ``omega_par`` is along ``v_hat``.
    Only ``omega_perp`` contributes to the Magnus force (SPEC §8.5).

    Args:
        omega: 3-vector angular velocity.
        v_hat: Unit velocity direction (need not be exactly unit; will be
            normalized).

    Returns:
        ``(omega_perp, omega_par)``, both 3-vectors.
    """
    v_hat_norm = v_hat / np.linalg.norm(v_hat)
    omega_par = float(np.dot(omega, v_hat_norm)) * v_hat_norm
    omega_perp = omega - omega_par
    return omega_perp, omega_par
