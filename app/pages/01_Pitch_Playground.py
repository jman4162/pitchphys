"""Pitch Playground — the master sandbox.

Composes every knob the engine exposes: pitch sliders, model selector,
forces toggles, environment, spin decay, animation. Renders the full
3D scene with spin-axis arrow + force-vector overlays plus a 2x2
matplotlib grid below.
"""

from __future__ import annotations

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
    "one shapes the path."
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

# ----- Break metrics row -----
render_break_metrics(traj)

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
