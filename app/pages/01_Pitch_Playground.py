"""Pitch Playground — the master sandbox.

Composes every knob the engine exposes: pitch sliders, model selector,
forces toggles, environment, spin decay, animation. Renders the full
3D scene with spin-axis arrow + force-vector overlays plus a 2x2
matplotlib grid below. Adds a strike-zone chip, download buttons, and a
Statcast comparison expander for credibility-checking the simulation.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils import (
    aero_model_selector,
    cached_simulate,
    environment_sidebar,
    forces_selector,
    pitch_release_sidebar,
    render_break_metrics,
    render_download_buttons,
    render_strike_zone_chip,
    spin_decay_sidebar,
)

from pitchphys.viz.animation import animate_pitch
from pitchphys.viz.plot2d import (
    catcher_view,
    side_view,
    top_view,
)
from pitchphys.viz.plot3d import (
    add_force_vectors,
    add_spin_axis_arrow,
    trajectory_3d,
)

st.title("Pitch Playground")
st.markdown(
    "Drag any slider — every plot below updates. Toggle the animation to "
    "watch the ball travel, or untoggle individual forces to see how each "
    "one shapes the path. **The URL captures every slider value, so you can "
    "share a link to your exact pitch.**"
)

pitch = pitch_release_sidebar(prefix="pp_")
model = aero_model_selector(prefix="pp_")
forces = forces_selector(prefix="pp_")
env = environment_sidebar(prefix="pp_")
tau = spin_decay_sidebar(prefix="pp_")
animate = st.sidebar.checkbox("Animate ball flight", value=False)

if not forces:
    st.warning("Select at least one force in the sidebar to simulate a trajectory.")
    st.stop()

traj = cached_simulate(pitch, env, model=model, forces=forces, spin_decay_tau_s=tau)

# ----- 3D scene -----
if animate:
    fig3d = animate_pitch(traj)
else:
    fig3d = trajectory_3d(traj, label="trajectory")
    add_spin_axis_arrow(fig3d, pitch, length_ft=2.5)
    if "magnus" in forces or "drag" in forces:
        # Show force overlays at three midflight times.
        ts = np.linspace(traj.time[0], traj.time[-1], 5)[1:-1]
        add_force_vectors(fig3d, traj, times=tuple(ts), forces=tuple(forces))
fig3d.update_layout(height=600)
st.plotly_chart(fig3d, use_container_width=True)

# ----- Strike chip -----
render_strike_zone_chip(traj)

# ----- Break metrics row -----
render_break_metrics(traj)

# ----- Download buttons -----
st.markdown("##### Save this pitch")
render_download_buttons(traj, fig3d=fig3d, prefix="pp_")

# ----- Statcast comparison expander -----
with st.expander("Compare to a real pitch (Statcast / Baseball Savant)", expanded=False):
    st.markdown(
        "Paste values from Baseball Savant for any pitch (e.g., a Spencer "
        "Strider fastball: 98 mph, 2400 rpm, 1:00 tilt, IVB +19 in, "
        "horizontal break -3 in) to see how close the simulation lands."
    )
    obs_col, sim_col, delta_col = st.columns(3)

    obs_col.markdown("**Observed**")
    obs_speed = obs_col.number_input(
        "Release speed (mph)",
        min_value=40.0,
        max_value=110.0,
        value=95.0,
        step=0.1,
        key="obs_speed",
    )
    obs_spin = obs_col.number_input(
        "Spin rate (rpm)",
        min_value=500.0,
        max_value=4000.0,
        value=2400.0,
        step=10.0,
        key="obs_spin",
    )
    obs_tilt = obs_col.number_input(
        "Tilt (clock hours)",
        min_value=0.0,
        max_value=12.0,
        value=12.0,
        step=0.25,
        key="obs_tilt",
    )
    obs_ivb = obs_col.number_input("IVB (in)", value=18.0, step=0.5, key="obs_ivb")
    obs_hb = obs_col.number_input("Horizontal break (in)", value=0.0, step=0.5, key="obs_hb")

    sim_spin_rpm = traj.pitch.spin_rate_rad_s * 60.0 / (2.0 * math.pi)
    sim_tilt = float(traj.pitch.metadata.get("tilt_clock", 12.0))
    sim_col.markdown("**Simulated**")
    sim_col.metric("Release speed", f"{traj.release_speed_mph:.1f} mph")
    sim_col.metric("Spin rate", f"{sim_spin_rpm:.0f} rpm")
    sim_col.metric("Tilt", f"{sim_tilt:.2f} hrs")
    sim_col.metric("IVB", f"{traj.induced_vertical_break_in:+.1f} in")
    sim_col.metric("Horiz break", f"{traj.horizontal_break_in:+.1f} in")

    delta_col.markdown("**Δ (sim − obs)**")
    delta_col.metric("Speed", f"{traj.release_speed_mph - obs_speed:+.1f} mph")
    delta_col.metric("Spin rate", f"{sim_spin_rpm - obs_spin:+.0f} rpm")
    delta_col.metric("Tilt", f"{sim_tilt - obs_tilt:+.2f} hrs")
    delta_col.metric("IVB", f"{traj.induced_vertical_break_in - obs_ivb:+.1f} in")
    delta_col.metric("Horiz break", f"{traj.horizontal_break_in - obs_hb:+.1f} in")

    st.caption(
        "If the Δ column is small (≤ 2 in. on IVB / horizontal break, "
        "≤ 1 mph on speed), the default `LyuAeroModel` is reproducing "
        "the real pitch's break well. Larger gaps usually mean active "
        "spin % or seam-shifted-wake effects matter for that pitch."
    )

# ----- 2D grid -----
st.markdown("### 2D views and force decomposition")
fig_grid, axes = plt.subplots(2, 2, figsize=(11, 8))
side_view(traj, ax=axes[0, 0])
axes[0, 0].set_title("Side view")
catcher_view(traj, ax=axes[0, 1])
axes[0, 1].set_title("Catcher view")
top_view(traj, ax=axes[1, 0])
axes[1, 0].set_title("Top view")

ax_f = axes[1, 1]
for fname, color in (("gravity", "tab:gray"), ("drag", "tab:orange"), ("magnus", "tab:blue")):
    if fname in traj.forces:
        mag = np.linalg.norm(traj.forces[fname], axis=1)
        ax_f.plot(traj.time, mag, label=fname, color=color)
ax_f.set_xlabel("t (s)")
ax_f.set_ylabel("|F| (N)")
ax_f.set_title("Force magnitudes vs. time")
ax_f.legend(loc="best")
ax_f.grid(True, alpha=0.3)
fig_grid.tight_layout()
st.pyplot(fig_grid)

# ----- Provenance footer -----
st.caption(
    f"Model: `{model}` · Forces: {', '.join(forces) if forces else '(none)'} · "
    f"Air density: {env.air_density_kg_m3:.4f} kg/m³ · "
    f"τ: {'∞ (constant ω)' if tau is None else f'{tau:.2f} s'}"
)
