"""Pitch release conditions (SPEC §9.3)."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Literal

import numpy as np

from pitchphys.coordinates import build_omega, clock_tilt_to_axis, decompose_omega
from pitchphys.units import ft_to_m, mph_to_mps, rpm_to_radps


@dataclass(frozen=True, slots=True)
class PitchRelease:
    """Release-time state of a pitched ball.

    Internally everything is SI: meters, seconds, kilograms, radians. Use
    :meth:`from_mph_rpm_axis` to construct from baseball-friendly units.
    """

    speed_m_s: float
    launch_angle_deg: float
    horizontal_angle_deg: float
    release_pos_m: np.ndarray
    spin_rate_rad_s: float
    spin_axis: np.ndarray  # full 3D unit vector (active + gyro mixed)
    active_spin_fraction: float = 1.0
    metadata: dict[str, float | str] = field(default_factory=dict)

    @classmethod
    def from_mph_rpm_axis(
        cls,
        speed_mph: float,
        spin_rpm: float,
        tilt_clock: float = 12.0,
        active_spin_fraction: float = 0.95,
        release_height_ft: float = 6.0,
        release_side_ft: float = -1.5,
        extension_ft: float = 6.0,  # informational in v0.1; release placed at y=0
        launch_angle_deg: float = -1.0,
        horizontal_angle_deg: float = 0.0,
        throwing_hand: Literal["R", "L"] = "R",
    ) -> PitchRelease:
        """Construct a PitchRelease from baseball-friendly units.

        ``tilt_clock`` is the clock-face tilt of the active spin axis viewed
        from behind home plate (catcher view). See :mod:`pitchphys.coordinates`
        for the convention. 12:00 = pure backspin axis, 6:00 = pure topspin,
        etc.

        The release position is at world ``y = 0``; the plate sits ahead at
        ``y = DEFAULT_PLATE_DISTANCE_M`` (55 ft). ``extension_ft`` is stored as
        metadata in v0.1 but does not shift the release point.

        Args:
            speed_mph: Pitch release speed.
            spin_rpm: Total spin rate (active + gyro).
            tilt_clock: Active-spin clock tilt in hours, 0..12.
            active_spin_fraction: Fraction of spin perpendicular to velocity
                (the part that produces Magnus break). 0 = pure gyro, 1 = pure
                active.
            release_height_ft: Height of release above home plate (z, ft).
            release_side_ft: Lateral release offset (x, ft). Negative = catcher's
                left, which is the typical RHP release side.
            extension_ft: Pitcher extension off the rubber (informational).
            launch_angle_deg: Angle of velocity above horizontal at release.
            horizontal_angle_deg: Yaw of velocity around vertical (positive
                toward +x).
            throwing_hand: ``"R"`` or ``"L"``; passed to :func:`clock_tilt_to_axis`.
        """
        speed_m_s = float(mph_to_mps(speed_mph))
        spin_rate = float(rpm_to_radps(spin_rpm))
        release_pos = np.array(
            [
                ft_to_m(release_side_ft),
                0.0,
                ft_to_m(release_height_ft),
            ],
            dtype=float,
        )

        v_hat = _direction_from_angles(launch_angle_deg, horizontal_angle_deg)
        active_axis = clock_tilt_to_axis(tilt_clock, throwing_hand=throwing_hand)
        omega = build_omega(spin_rate, active_axis, active_spin_fraction, v_hat)
        omega_norm = np.linalg.norm(omega)
        spin_axis_unit = omega / omega_norm if omega_norm > 0 else active_axis

        return cls(
            speed_m_s=speed_m_s,
            launch_angle_deg=float(launch_angle_deg),
            horizontal_angle_deg=float(horizontal_angle_deg),
            release_pos_m=release_pos,
            spin_rate_rad_s=spin_rate,
            spin_axis=spin_axis_unit,
            active_spin_fraction=float(active_spin_fraction),
            metadata={
                "extension_ft": float(extension_ft),
                "throwing_hand": str(throwing_hand).upper(),
                "tilt_clock": float(tilt_clock),
            },
        )

    def initial_velocity(self) -> np.ndarray:
        """Initial velocity 3-vector in world frame (m/s)."""
        v_hat = _direction_from_angles(self.launch_angle_deg, self.horizontal_angle_deg)
        return self.speed_m_s * v_hat

    def omega_vec(self, v_hat: np.ndarray | None = None) -> np.ndarray:
        """Angular velocity 3-vector in world frame (rad/s).

        If ``v_hat`` is given, the omega vector is reconstructed from the
        active axis + active_spin_fraction so the perp/parallel decomposition
        matches the requested velocity direction. Otherwise we use the stored
        ``spin_axis`` scaled by ``spin_rate_rad_s``.
        """
        if v_hat is None:
            return self.spin_rate_rad_s * self.spin_axis
        # Recover the active-axis unit vector from spin_axis by removing the
        # gyro component aligned with this v_hat. For pitches whose v_hat at
        # call time matches the v_hat used at construction, this returns the
        # same omega; for slightly different v_hat it re-projects.
        v_hat_norm = v_hat / np.linalg.norm(v_hat)
        omega_full = self.spin_rate_rad_s * self.spin_axis
        perp, _ = decompose_omega(omega_full, v_hat_norm)
        perp_norm = np.linalg.norm(perp)
        if perp_norm < 1e-12:
            # Pitch is pure gyro from this view; nothing to rebuild.
            return omega_full
        active_axis = perp / perp_norm
        return build_omega(self.spin_rate_rad_s, active_axis, self.active_spin_fraction, v_hat_norm)


def _direction_from_angles(launch_deg: float, horizontal_deg: float) -> np.ndarray:
    """Unit vector from launch (above horizontal) and horizontal (yaw) angles."""
    launch = math.radians(launch_deg)
    yaw = math.radians(horizontal_deg)
    return np.array(
        [
            math.cos(launch) * math.sin(yaw),
            math.cos(launch) * math.cos(yaw),
            math.sin(launch),
        ]
    )
