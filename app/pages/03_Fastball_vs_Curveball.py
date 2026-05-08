"""Two-pitch side-by-side comparison."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils import (
    cached_simulate,
    render_download_buttons,
    render_strike_zone_chip,
)

from pitchphys import presets
from pitchphys.core.environment import Environment
from pitchphys.core.pitch import PitchRelease
from pitchphys.viz.plot2d import compare_pitches
from pitchphys.viz.plot3d import compare_pitches_3d

st.title("Fastball vs Curveball")
st.markdown(
    "Pick two pitch archetypes (or build them from scratch) and compare "
    "trajectories side by side in 3D and from the catcher's view."
)

_PRESETS = {
    "four_seam": presets.four_seam,
    "curveball": presets.curveball,
    "slider": presets.slider,
    "sinker": presets.sinker,
    "changeup": presets.changeup,
}


def _pitch_inputs(label: str, default_preset: str, defaults: dict) -> PitchRelease:
    st.subheader(label)
    preset_name = st.selectbox(
        "Preset",
        list(_PRESETS),
        index=list(_PRESETS).index(default_preset),
        key=f"{label}_preset",
    )
    speed = st.slider(
        "Speed (mph)",
        60.0,
        105.0,
        defaults["speed"],
        0.5,
        key=f"{label}_speed",
    )
    spin = st.slider(
        "Spin rate (rpm)",
        1000.0,
        3500.0,
        defaults["spin"],
        50.0,
        key=f"{label}_spin",
    )
    tilt = st.slider(
        "Tilt (clock)",
        0.0,
        12.0,
        defaults["tilt"],
        0.25,
        key=f"{label}_tilt",
    )
    active = st.slider(
        "Active spin fraction",
        0.0,
        1.0,
        defaults["active"],
        0.05,
        key=f"{label}_active",
    )
    hand = st.radio(
        "Throwing hand",
        ("R", "L"),
        horizontal=True,
        key=f"{label}_hand",
    )
    return _PRESETS[preset_name](
        speed_mph=speed,
        spin_rpm=spin,
        tilt_clock=tilt,
        active_spin_fraction=active,
        throwing_hand=hand,
    )


col_a, col_b = st.columns(2)
with col_a:
    pitch_a = _pitch_inputs(
        "Pitch A",
        "four_seam",
        {"speed": 95.0, "spin": 2400.0, "tilt": 12.0, "active": 0.95},
    )
with col_b:
    pitch_b = _pitch_inputs(
        "Pitch B",
        "curveball",
        {"speed": 80.0, "spin": 2700.0, "tilt": 6.0, "active": 0.85},
    )

env = Environment.sea_level()
traj_a = cached_simulate(pitch_a, env)
traj_b = cached_simulate(pitch_b, env)

st.markdown("### 3D comparison")
fig3d = compare_pitches_3d([traj_a, traj_b], labels=["Pitch A", "Pitch B"])
st.plotly_chart(fig3d, use_container_width=True)

# ----- Strike chips per pitch -----
chip_col_a, chip_col_b = st.columns(2)
with chip_col_a:
    st.markdown("**Pitch A**")
    render_strike_zone_chip(traj_a)
with chip_col_b:
    st.markdown("**Pitch B**")
    render_strike_zone_chip(traj_b)

st.markdown("### 2D views")
view_col_a, view_col_b = st.columns(2)
with view_col_a:
    fig_catcher = compare_pitches([traj_a, traj_b], view="catcher", labels=["A", "B"])
    st.pyplot(fig_catcher.figure if hasattr(fig_catcher, "figure") else fig_catcher.get_figure())
with view_col_b:
    fig_side = compare_pitches([traj_a, traj_b], view="side", labels=["A", "B"])
    st.pyplot(fig_side.figure if hasattr(fig_side, "figure") else fig_side.get_figure())

st.markdown("### Break metrics")
metrics_col = st.columns(3)
metrics_col[0].markdown("**Pitch A**")
metrics_col[0].metric("Plate", f"{traj_a.plate_speed_mph:.1f} mph")
metrics_col[0].metric("IVB", f"{traj_a.induced_vertical_break_in:+.1f} in")
metrics_col[0].metric("Horiz", f"{traj_a.horizontal_break_in:+.1f} in")
metrics_col[0].metric("Drop", f"{traj_a.total_drop_in:.1f} in")

metrics_col[1].markdown("**Pitch B**")
metrics_col[1].metric("Plate", f"{traj_b.plate_speed_mph:.1f} mph")
metrics_col[1].metric("IVB", f"{traj_b.induced_vertical_break_in:+.1f} in")
metrics_col[1].metric("Horiz", f"{traj_b.horizontal_break_in:+.1f} in")
metrics_col[1].metric("Drop", f"{traj_b.total_drop_in:.1f} in")

metrics_col[2].markdown("**Δ (A − B)**")
metrics_col[2].metric(
    "Plate",
    f"{traj_a.plate_speed_mph - traj_b.plate_speed_mph:+.1f} mph",
)
metrics_col[2].metric(
    "IVB",
    f"{traj_a.induced_vertical_break_in - traj_b.induced_vertical_break_in:+.1f} in",
)
metrics_col[2].metric(
    "Horiz",
    f"{traj_a.horizontal_break_in - traj_b.horizontal_break_in:+.1f} in",
)
metrics_col[2].metric(
    "Drop",
    f"{traj_a.total_drop_in - traj_b.total_drop_in:+.1f} in",
)

# ----- Per-pitch download buttons -----
st.markdown("### Save these pitches")
dl_col_a, dl_col_b = st.columns(2)
with dl_col_a:
    st.markdown("**Pitch A**")
    render_download_buttons(traj_a, fig3d=None, prefix="fbcv_a_")
with dl_col_b:
    st.markdown("**Pitch B**")
    render_download_buttons(traj_b, fig3d=None, prefix="fbcv_b_")
