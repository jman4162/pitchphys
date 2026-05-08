"""Streamlit widgets, cache wrapper, and rendering helpers shared by the
pages of the pitchphys educational app.

This module is imported by every ``app/pages/*.py`` file. Pure helper
functions for cache-key derivation, strike-zone classification, CSV
serialization, and URL state encoding live in
:mod:`pitchphys._app_helpers` so they're testable without Streamlit
installed.
"""

from __future__ import annotations

import contextlib
import json

import numpy as np
import streamlit as st

from pitchphys import simulate
from pitchphys._app_helpers import (
    CANONICAL_PITCH_KEYS,
    env_to_key,
    is_strike,
    pack_url_params,
    pitch_to_key,
    trajectory_to_csv,
    unpack_url_params,
)
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

_CANONICAL_PITCH_DEFAULTS: dict[str, object] = {
    "speed_mph": 95.0,
    "spin_rpm": 2400.0,
    "tilt_clock": 12.0,
    "active_spin_fraction": 0.95,
    "release_height_ft": 6.0,
    "release_side_ft": -1.5,
    "throwing_hand": "R",
}


# ---------------------------------------------------------------------------
# Canonical pitch state (cross-page persistence + URL encoding)
# ---------------------------------------------------------------------------


def _seed_canonical_from_url() -> dict[str, object]:
    """Read URL query params on first render; merge into session state.

    Streamlit reruns the script on every widget change, so we only seed
    from URL once per session — subsequent renders use session_state as
    the source of truth and write back to the URL.
    """
    if "canonical_pitch" in st.session_state:
        return st.session_state["canonical_pitch"]

    canonical = _CANONICAL_PITCH_DEFAULTS.copy()
    try:
        params = dict(st.query_params)
    except Exception:
        params = {}
    canonical.update(unpack_url_params(params))
    st.session_state["canonical_pitch"] = canonical
    return canonical


def _write_canonical_to_url(canonical: dict[str, object]) -> None:
    """Persist canonical pitch state into the URL for shareability.

    Older Streamlit versions / non-browser environments may not support
    ``st.query_params`` writes; we silently swallow errors there.
    """
    with contextlib.suppress(Exception):
        st.query_params.update(pack_url_params(canonical))


def get_canonical_pitch() -> dict[str, object]:
    """Public accessor: returns the live canonical-pitch dict."""
    return _seed_canonical_from_url()


# ---------------------------------------------------------------------------
# Sidebar widgets
# ---------------------------------------------------------------------------


def pitch_release_sidebar(
    *,
    prefix: str = "",
    expanded: bool = True,
    use_canonical: bool = True,
) -> PitchRelease:
    """Render pitch-release sliders in the sidebar; return the built pitch.

    When ``use_canonical=True`` (default), slider defaults come from
    :data:`st.session_state["canonical_pitch"]` — so values persist
    across pages and via URL. Page-specific widgets (with
    ``use_canonical=False``) keep page-local state only.
    """
    canonical = _seed_canonical_from_url() if use_canonical else _CANONICAL_PITCH_DEFAULTS

    with st.sidebar.expander("Pitch release", expanded=expanded):
        speed_mph = st.slider(
            "Speed (mph)",
            60.0,
            105.0,
            float(canonical["speed_mph"]),
            0.5,
            key=f"{prefix}speed",
        )
        spin_rpm = st.slider(
            "Spin rate (rpm)",
            1000.0,
            3500.0,
            float(canonical["spin_rpm"]),
            50.0,
            key=f"{prefix}spin",
        )
        tilt_clock = st.slider(
            "Tilt (clock face, hours)",
            0.0,
            12.0,
            float(canonical["tilt_clock"]),
            0.25,
            key=f"{prefix}tilt",
            help="12:00 = pure backspin, 6:00 = pure topspin (catcher view)",
        )
        active_spin_fraction = st.slider(
            "Active spin fraction",
            0.0,
            1.0,
            float(canonical["active_spin_fraction"]),
            0.05,
            key=f"{prefix}active",
            help="0 = pure gyro (no Magnus break); 1 = all spin perpendicular to v",
        )
        throwing_hand = st.radio(
            "Throwing hand",
            ("R", "L"),
            index=0 if canonical["throwing_hand"] == "R" else 1,
            horizontal=True,
            key=f"{prefix}hand",
        )
        release_height_ft = st.slider(
            "Release height (ft)",
            4.5,
            7.5,
            float(canonical["release_height_ft"]),
            0.1,
            key=f"{prefix}rel_h",
        )
        release_side_ft = st.slider(
            "Release side (ft)",
            -3.0,
            3.0,
            float(canonical["release_side_ft"]),
            0.1,
            key=f"{prefix}rel_s",
            help="Negative = catcher's left (typical RHP).",
        )

    if use_canonical:
        canonical.update(
            {
                "speed_mph": float(speed_mph),
                "spin_rpm": float(spin_rpm),
                "tilt_clock": float(tilt_clock),
                "active_spin_fraction": float(active_spin_fraction),
                "release_height_ft": float(release_height_ft),
                "release_side_ft": float(release_side_ft),
                "throwing_hand": throwing_hand,
            }
        )
        _write_canonical_to_url(canonical)

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


def render_strike_zone_chip(traj: TrajectoryResult) -> None:
    """Display a colored chip indicating ball or strike at plate."""
    if is_strike(traj.plate_x_ft, traj.plate_z_ft):
        st.success(
            f"⚾ **STRIKE** — pitch crossed the zone at "
            f"({traj.plate_x_ft:+.2f}, {traj.plate_z_ft:.2f}) ft"
        )
    else:
        st.warning(
            f"⚪ **Ball** — pitch crossed at "
            f"({traj.plate_x_ft:+.2f}, {traj.plate_z_ft:.2f}) ft, outside the zone"
        )


def render_3d(fig: object, *, height: int = 600) -> None:
    """Render a Plotly figure full-width."""
    st.plotly_chart(fig, use_container_width=True, height=height)


def render_mpl(fig: object) -> None:
    """Render a matplotlib figure inside a Streamlit container."""
    st.pyplot(fig, clear_figure=False)


def render_download_buttons(
    traj: TrajectoryResult,
    fig3d: object | None = None,
    *,
    prefix: str = "",
) -> None:
    """Render trajectory CSV / 3D HTML / break-metrics JSON download buttons.

    ``fig3d`` is optional; if absent only the CSV and JSON buttons appear.
    """
    cols = st.columns(3 if fig3d is not None else 2)
    csv_data = trajectory_to_csv(traj)
    cols[0].download_button(
        "⬇ Trajectory CSV",
        csv_data,
        file_name="trajectory.csv",
        mime="text/csv",
        key=f"{prefix}dl_csv",
    )
    json_data = json.dumps(traj.break_metrics(), indent=2)
    cols[1].download_button(
        "⬇ Break metrics (JSON)",
        json_data,
        file_name="break_metrics.json",
        mime="application/json",
        key=f"{prefix}dl_json",
    )
    if fig3d is not None:
        cols[2].download_button(
            "⬇ 3D figure (HTML)",
            fig3d.to_html(include_plotlyjs="cdn"),  # type: ignore[attr-defined]
            file_name="trajectory_3d.html",
            mime="text/html",
            key=f"{prefix}dl_html",
        )


__all__ = [
    "CANONICAL_PITCH_KEYS",
    "aero_model_selector",
    "cached_simulate",
    "environment_sidebar",
    "forces_selector",
    "get_canonical_pitch",
    "is_strike",
    "pitch_release_sidebar",
    "render_3d",
    "render_break_metrics",
    "render_download_buttons",
    "render_mpl",
    "render_strike_zone_chip",
    "spin_decay_sidebar",
    "wind_sidebar",
]
