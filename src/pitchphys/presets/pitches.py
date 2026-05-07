"""Pedagogical pitch presets.

These defaults are **archetypes**, not MLB averages. Override speed, spin,
tilt, or active-spin fraction to model a specific pitcher. The presets exist
to give users a quick handle on representative four-seam, curveball, slider,
sinker, and changeup behavior under the package's clock-tilt convention.

Tilt values (RHP, catcher view per :mod:`pitchphys.coordinates`):

================  ==========  =============================
Pitch             tilt_clock  Magnus break direction
================  ==========  =============================
four_seam         12.0        straight up (lift)
curveball          6.0        straight down (drop)
slider             3.0        catcher's right; mostly gyro
sinker             7.5        arm-side + drop (RHP -x, -z)
changeup           7.0        arm-side + slight drop
================  ==========  =============================

For LHP, pass ``throwing_hand="L"`` and the resulting axis mirrors across the
12-6 line.
"""

from __future__ import annotations

from typing import Any, Literal

from pitchphys.core.pitch import PitchRelease


def four_seam(
    speed_mph: float = 95.0,
    spin_rpm: float = 2400.0,
    tilt_clock: float = 12.0,
    active_spin_fraction: float = 0.95,
    throwing_hand: Literal["R", "L"] = "R",
    **kwargs: Any,
) -> PitchRelease:
    """High-spin backspin fastball. Default Magnus break: straight up."""
    return PitchRelease.from_mph_rpm_axis(
        speed_mph=speed_mph,
        spin_rpm=spin_rpm,
        tilt_clock=tilt_clock,
        active_spin_fraction=active_spin_fraction,
        throwing_hand=throwing_hand,
        **kwargs,
    )


def curveball(
    speed_mph: float = 80.0,
    spin_rpm: float = 2700.0,
    tilt_clock: float = 6.0,
    active_spin_fraction: float = 0.85,
    throwing_hand: Literal["R", "L"] = "R",
    **kwargs: Any,
) -> PitchRelease:
    """Topspin curveball. Default Magnus break: straight down."""
    return PitchRelease.from_mph_rpm_axis(
        speed_mph=speed_mph,
        spin_rpm=spin_rpm,
        tilt_clock=tilt_clock,
        active_spin_fraction=active_spin_fraction,
        throwing_hand=throwing_hand,
        **kwargs,
    )


def slider(
    speed_mph: float = 85.0,
    spin_rpm: float = 2500.0,
    tilt_clock: float = 3.0,
    active_spin_fraction: float = 0.30,
    throwing_hand: Literal["R", "L"] = "R",
    **kwargs: Any,
) -> PitchRelease:
    """Gyro-dominant slider. High raw spin, low total break.

    Demonstrates SPEC §4.4: spin rate alone does not predict movement.
    """
    return PitchRelease.from_mph_rpm_axis(
        speed_mph=speed_mph,
        spin_rpm=spin_rpm,
        tilt_clock=tilt_clock,
        active_spin_fraction=active_spin_fraction,
        throwing_hand=throwing_hand,
        **kwargs,
    )


def sinker(
    speed_mph: float = 92.0,
    spin_rpm: float = 2200.0,
    tilt_clock: float = 7.5,
    active_spin_fraction: float = 0.85,
    throwing_hand: Literal["R", "L"] = "R",
    **kwargs: Any,
) -> PitchRelease:
    """Arm-side sinker for RHP. Default break: arm side + drop."""
    return PitchRelease.from_mph_rpm_axis(
        speed_mph=speed_mph,
        spin_rpm=spin_rpm,
        tilt_clock=tilt_clock,
        active_spin_fraction=active_spin_fraction,
        throwing_hand=throwing_hand,
        **kwargs,
    )


def changeup(
    speed_mph: float = 84.0,
    spin_rpm: float = 1700.0,
    tilt_clock: float = 7.0,
    active_spin_fraction: float = 0.80,
    throwing_hand: Literal["R", "L"] = "R",
    **kwargs: Any,
) -> PitchRelease:
    """Off-speed changeup. Lower spin, slight arm-side run + drop."""
    return PitchRelease.from_mph_rpm_axis(
        speed_mph=speed_mph,
        spin_rpm=spin_rpm,
        tilt_clock=tilt_clock,
        active_spin_fraction=active_spin_fraction,
        throwing_hand=throwing_hand,
        **kwargs,
    )
