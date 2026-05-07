"""Streamlit-app helpers that don't require Streamlit at import time.

These live inside the installed package (rather than under ``app/``) so
tests can import them without setting up Streamlit. The widget code in
``app/utils.py`` calls into these for cache-key derivation.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pitchphys.core.environment import Environment
    from pitchphys.core.pitch import PitchRelease


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
