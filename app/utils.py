"""Streamlit widgets, cache wrapper, and rendering helpers shared by the
pages of the pitchphys educational app.

This module is imported by every ``app/pages/*.py`` file. Pure helper
functions for cache-key derivation live in :mod:`pitchphys._app_helpers`
so they're testable without Streamlit installed.
"""

from __future__ import annotations

import numpy as np
import streamlit as st

from pitchphys import simulate
from pitchphys._app_helpers import env_to_key, pitch_to_key
from pitchphys.constants import DEFAULT_PLATE_DISTANCE_M
from pitchphys.core.environment import Environment
from pitchphys.core.pitch import PitchRelease
from pitchphys.core.trajectory import TrajectoryResult

_MODEL_CHOICES = ("magnus", "lyu", "nathan", "simple", "constant")
_MODEL_DESCRIPTIONS = {
    "magnus": "LyuAeroModel (default) — Lyu 2022 wind-tunnel fit",
    "lyu": "LyuAeroModel — explicit alias",
    "nathan": "NathanLiftModel — Sawicki bilinear C_L(S)",
    "simple": "SimpleMagnusModel — pedagogical Cl ≈ S",
    "constant": "ConstantAeroModel — Cd=0.35, Cl=0.20",
}


# ---------------------------------------------------------------------------
# Sidebar widgets
# ---------------------------------------------------------------------------


def pitch_release_sidebar(
    *,
    prefix: str = "",
    speed_default: float = 95.0,
    spin_default: float = 2400.0,
    tilt_default: float = 12.0,
    active_default: float = 0.95,
    expanded: bool = True,
) -> PitchRelease:
    """Render pitch-release sliders in the sidebar; return the built pitch."""
    with st.sidebar.expander("Pitch release", expanded=expanded):
        speed_mph = st.slider("Speed (mph)", 60.0, 105.0, speed_default, 0.5, key=f"{prefix}speed")
        spin_rpm = st.slider(
            "Spin rate (rpm)", 1000.0, 3500.0, spin_default, 50.0, key=f"{prefix}spin"
        )
        tilt_clock = st.slider(
            "Tilt (clock face, hours)",
            0.0,
            12.0,
            tilt_default,
            0.25,
            key=f"{prefix}tilt",
            help="12:00 = pure backspin, 6:00 = pure topspin (catcher view)",
        )
        active_spin_fraction = st.slider(
            "Active spin fraction",
            0.0,
            1.0,
            active_default,
            0.05,
            key=f"{prefix}active",
            help="0 = pure gyro (no Magnus break); 1 = all spin perpendicular to v",
        )
        throwing_hand = st.radio("Throwing hand", ("R", "L"), horizontal=True, key=f"{prefix}hand")
        release_height_ft = st.slider(
            "Release height (ft)", 4.5, 7.5, 6.0, 0.1, key=f"{prefix}rel_h"
        )
        release_side_ft = st.slider(
            "Release side (ft)",
            -3.0,
            3.0,
            -1.5,
            0.1,
            key=f"{prefix}rel_s",
            help="Negative = catcher's left (typical RHP).",
        )
    return PitchRelease.from_mph_rpm_axis(
        speed_mph=speed_mph,
        spin_rpm=spin_rpm,
        tilt_clock=tilt_clock,
        active_spin_fraction=active_spin_fraction,
        release_height_ft=release_height_ft,
        release_side_ft=release_side_ft,
        throwing_hand=throwing_hand,
    )


def environment_sidebar(*, prefix: str = "") -> Environment:
    """Render environment selector + optional weather sliders."""
    with st.sidebar.expander("Environment", expanded=False):
        choice = st.radio(
            "Air conditions",
            ("Sea level", "Coors Field", "Custom (from_weather)"),
            key=f"{prefix}env_choice",
        )
        if choice == "Sea level":
            return Environment.sea_level()
        if choice == "Coors Field":
            return Environment.coors_field()
        # Custom weather
        temp_c = st.slider("Temp (°C)", -10.0, 40.0, 20.0, 0.5, key=f"{prefix}temp")
        pressure_pa = st.slider(
            "Pressure (Pa)",
            60000.0,
            105000.0,
            101325.0,
            500.0,
            key=f"{prefix}pressure",
        )
        humidity = st.slider("Relative humidity", 0.0, 1.0, 0.4, 0.05, key=f"{prefix}humidity")
        return Environment.from_weather(temp_c, pressure_pa, humidity)


def aero_model_selector(*, prefix: str = "") -> str:
    """Single selectbox for the lift/drag model."""
    return str(
        st.sidebar.selectbox(
            "Aerodynamic model",
            options=list(_MODEL_CHOICES),
            format_func=lambda v: _MODEL_DESCRIPTIONS.get(v, v),
            key=f"{prefix}model",
        )
    )


def forces_selector(*, prefix: str = "") -> tuple[str, ...]:
    """Multi-select for which forces to include in the simulation."""
    chosen = st.sidebar.multiselect(
        "Forces",
        options=["gravity", "drag", "magnus"],
        default=["gravity", "drag", "magnus"],
        key=f"{prefix}forces",
    )
    return tuple(chosen)


def spin_decay_sidebar(*, prefix: str = "", default_tau: float | None = 1.5) -> float | None:
    """Slider + checkbox to set or disable spin decay."""
    with st.sidebar.expander("Spin decay", expanded=False):
        disabled = st.checkbox(
            "Disable (constant ω)",
            value=default_tau is None,
            key=f"{prefix}tau_off",
        )
        if disabled:
            return None
        tau = st.slider("τ (s)", 0.5, 5.0, default_tau or 1.5, 0.1, key=f"{prefix}tau")
        return float(tau)


def wind_sidebar(*, prefix: str = "") -> np.ndarray:
    """Three-axis wind sliders (m/s)."""
    with st.sidebar.expander("Wind (m/s)", expanded=False):
        wx = st.slider("vx (catcher's right)", -10.0, 10.0, 0.0, 0.5, key=f"{prefix}wx")
        wy = st.slider("vy (toward plate)", -10.0, 10.0, 0.0, 0.5, key=f"{prefix}wy")
        wz = st.slider("vz (vertical)", -5.0, 5.0, 0.0, 0.5, key=f"{prefix}wz")
    return np.array([wx, wy, wz])


# ---------------------------------------------------------------------------
# Cached simulate
# ---------------------------------------------------------------------------


@st.cache_data(
    show_spinner=False,
    hash_funcs={
        PitchRelease: pitch_to_key,
        Environment: env_to_key,
    },
)
def cached_simulate(
    pitch: PitchRelease,
    env: Environment,
    model: str = "magnus",
    forces: tuple[str, ...] | None = None,
    spin_decay_tau_s: float | None = 1.5,
    plate_distance_m: float = DEFAULT_PLATE_DISTANCE_M,
) -> TrajectoryResult:
    """Streamlit-cached wrapper around :func:`pitchphys.simulate`."""
    return simulate(
        pitch,
        env=env,
        model=model,
        forces=list(forces) if forces is not None else None,
        plate_distance_m=plate_distance_m,
        spin_decay_tau_s=spin_decay_tau_s,
    )


# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------


def render_break_metrics(traj: TrajectoryResult) -> None:
    """Show key break metrics in a compact row of st.metric widgets."""
    cols = st.columns(4)
    cols[0].metric("Release", f"{traj.release_speed_mph:.1f} mph")
    cols[1].metric("Plate", f"{traj.plate_speed_mph:.1f} mph")
    cols[2].metric("Flight time", f"{traj.flight_time_s:.2f} s")
    cols[3].metric("IVB", f"{traj.induced_vertical_break_in:+.1f} in")
    cols2 = st.columns(4)
    cols2[0].metric("Horiz break", f"{traj.horizontal_break_in:+.1f} in")
    cols2[1].metric("Total drop", f"{traj.total_drop_in:.1f} in")
    if traj.grav_drag_baseline is not None:
        cols2[2].metric("Magnus |break|", f"{traj.magnus_break_magnitude_in:.1f} in")
        cols2[3].metric(
            "Plate (x, z)",
            f"({traj.plate_x_ft:+.1f}, {traj.plate_z_ft:.1f}) ft",
        )
    else:
        cols2[2].metric(
            "Plate (x, z)",
            f"({traj.plate_x_ft:+.1f}, {traj.plate_z_ft:.1f}) ft",
        )


def render_3d(fig: object, *, height: int = 600) -> None:
    """Render a Plotly figure full-width."""
    st.plotly_chart(fig, use_container_width=True, height=height)


def render_mpl(fig: object) -> None:
    """Render a matplotlib figure inside a Streamlit container."""
    st.pyplot(fig, clear_figure=False)


__all__ = [
    "aero_model_selector",
    "cached_simulate",
    "environment_sidebar",
    "forces_selector",
    "pitch_release_sidebar",
    "render_3d",
    "render_break_metrics",
    "render_mpl",
    "spin_decay_sidebar",
    "wind_sidebar",
]
