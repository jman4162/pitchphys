"""Active-spin vs gyro-spin explorer.

Demonstrates SPEC §4.4: spin rate alone does not determine movement. Holds
total spin constant; sweeps the active-spin fraction (the share perpendicular
to velocity, which is what produces Magnus break) from 0 to 1.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

# Allow running both via `streamlit run` from the repo and via the installed
# console script (where app/ is bundled into pitchphys/_app/).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils import cached_simulate

from pitchphys.core.environment import Environment
from pitchphys.core.pitch import PitchRelease
from pitchphys.viz.plot3d import compare_pitches_3d

st.title("Active Spin vs Gyro Spin")
st.markdown(
    "Holding the **total spin rate** constant, sweep the **active spin "
    "fraction** from 0 to 1. The active fraction is the share of spin that "
    "is *perpendicular to velocity* — only that part contributes to Magnus "
    "break (SPEC §4.4)."
)

with st.sidebar:
    st.header("Pitch")
    speed_mph = st.slider("Speed (mph)", 70.0, 105.0, 92.0, 0.5)
    spin_rpm = st.slider("Total spin rate (rpm)", 1500.0, 3500.0, 2500.0, 50.0)
    tilt_clock = st.slider(
        "Tilt (clock face)",
        0.0,
        12.0,
        12.0,
        0.25,
        help="12:00 = backspin axis. Sweep is over active fraction at this tilt.",
    )
    throwing_hand = st.radio("Throwing hand", ("R", "L"), horizontal=True)
    n_samples = st.slider("Samples in sweep", 5, 41, 21, 2)

env = Environment.sea_level()
fractions = np.linspace(0.0, 1.0, n_samples)

trajs = []
for f in fractions:
    pitch = PitchRelease.from_mph_rpm_axis(
        speed_mph=speed_mph,
        spin_rpm=spin_rpm,
        tilt_clock=tilt_clock,
        active_spin_fraction=float(f),
        throwing_hand=throwing_hand,
    )
    trajs.append(cached_simulate(pitch, env))

ivbs = np.array([t.induced_vertical_break_in for t in trajs])
hbs = np.array([t.horizontal_break_in for t in trajs])
mags = np.hypot(ivbs, hbs)

# ----- Sweep line chart -----
sweep_fig = go.Figure()
sweep_fig.add_trace(
    go.Scatter(
        x=fractions,
        y=mags,
        name="|total break| (in)",
        mode="lines+markers",
        line={"color": "#1f77b4", "width": 3},
    )
)
sweep_fig.add_trace(
    go.Scatter(
        x=fractions,
        y=ivbs,
        name="IVB (in)",
        mode="lines+markers",
        line={"color": "#2ca02c"},
    )
)
sweep_fig.add_trace(
    go.Scatter(
        x=fractions,
        y=hbs,
        name="Horizontal break (in)",
        mode="lines+markers",
        line={"color": "#d62728"},
    )
)
sweep_fig.update_layout(
    xaxis_title="Active spin fraction",
    yaxis_title="Break (in)",
    title=f"Total spin held at {spin_rpm:.0f} rpm — only active fraction is changing",
    height=400,
    legend={"orientation": "h", "y": -0.15},
)
st.plotly_chart(sweep_fig, use_container_width=True)

# ----- 3D overlay at selected fractions -----
st.subheader("Trajectories at selected active-spin fractions")
overlay_fractions = [0.0, 0.25, 0.5, 0.75, 1.0]
overlay_trajs = []
overlay_labels = []
for f in overlay_fractions:
    p = PitchRelease.from_mph_rpm_axis(
        speed_mph=speed_mph,
        spin_rpm=spin_rpm,
        tilt_clock=tilt_clock,
        active_spin_fraction=float(f),
        throwing_hand=throwing_hand,
    )
    overlay_trajs.append(cached_simulate(p, env))
    overlay_labels.append(f"active = {f:.2f}")

fig3d = compare_pitches_3d(overlay_trajs, labels=overlay_labels)
st.plotly_chart(fig3d, use_container_width=True)

# ----- Pedagogical callout -----
st.markdown(
    f"""
    ### What you should see

    - At **active = 0** (pure gyro), the ball follows the no-Magnus path —
      total break ≈ {mags[0]:.1f} in. Some small movement still appears
      because gravity tilts `v_hat` mid-flight, so `ω` (held constant in
      world frame) develops a small perpendicular component.
    - At **active = 1**, the full Magnus break is realized — total break
      ≈ {mags[-1]:.1f} in.
    - The line is **monotone increasing**: more active spin always means
      more movement at this fixed total spin rate.

    This is why a "high-spin" pitch isn't automatically a high-movement
    pitch. A 2500 rpm gyro slider has tons of spin but very little break.
    """
)
