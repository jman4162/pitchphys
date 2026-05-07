"""Drag + environment explorer.

Compares three force-toggle scenarios (gravity-only, gravity+drag,
full physics) under user-selected atmospheric conditions and wind. Shows
how plate speed and IVB respond to each variable.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils import cached_simulate

from pitchphys.core.environment import Environment
from pitchphys.core.pitch import PitchRelease
from pitchphys.viz.plot3d import compare_pitches_3d

st.title("Drag + Environment")
st.markdown(
    "Compare three force scenarios under one set of atmospheric conditions: "
    "**gravity only**, **gravity + drag**, and **full physics** (gravity + "
    "drag + Magnus). See how each force adds to the trajectory."
)

# ----- Pitch -----
with st.sidebar:
    st.header("Pitch")
    speed_mph = st.slider("Speed (mph)", 60.0, 105.0, 95.0, 0.5)
    spin_rpm = st.slider("Spin rate (rpm)", 1000.0, 3500.0, 2400.0, 50.0)
    tilt_clock = st.slider("Tilt (clock)", 0.0, 12.0, 12.0, 0.25)
    active = st.slider("Active spin fraction", 0.0, 1.0, 0.95, 0.05)
    hand = st.radio("Throwing hand", ("R", "L"), horizontal=True)

# ----- Environment -----
with st.sidebar:
    st.header("Environment")
    env_choice = st.radio(
        "Air conditions",
        ("Sea level", "Coors Field", "Custom"),
    )
    if env_choice == "Custom":
        temp_c = st.slider("Temp (°C)", -10.0, 40.0, 20.0, 0.5)
        pressure_pa = st.slider("Pressure (Pa)", 60000.0, 105000.0, 101325.0, 500.0)
        humidity = st.slider("Relative humidity", 0.0, 1.0, 0.4, 0.05)
        env_base = Environment.from_weather(temp_c, pressure_pa, humidity)
    elif env_choice == "Coors Field":
        env_base = Environment.coors_field()
    else:
        env_base = Environment.sea_level()

    st.header("Wind (m/s)")
    wx = st.slider("vx (catcher's right)", -10.0, 10.0, 0.0, 0.5)
    wy = st.slider("vy (toward plate)", -10.0, 10.0, 0.0, 0.5)
    wz = st.slider("vz (vertical)", -5.0, 5.0, 0.0, 0.5)

env = Environment(
    air_density_kg_m3=env_base.air_density_kg_m3,
    dynamic_viscosity_pa_s=env_base.dynamic_viscosity_pa_s,
    gravity_m_s2=env_base.gravity_m_s2,
    wind_m_s=np.array([wx, wy, wz]),
)

pitch = PitchRelease.from_mph_rpm_axis(
    speed_mph=speed_mph,
    spin_rpm=spin_rpm,
    tilt_clock=tilt_clock,
    active_spin_fraction=active,
    throwing_hand=hand,
)

scenarios = [
    ("Gravity only", ("gravity",)),
    ("Gravity + drag", ("gravity", "drag")),
    ("Full physics", ("gravity", "drag", "magnus")),
]

trajs = [cached_simulate(pitch, env, forces=forces) for _, forces in scenarios]
labels = [name for name, _ in scenarios]

st.markdown(f"**Air density:** {env.air_density_kg_m3:.4f} kg/m³")

fig3d = compare_pitches_3d(trajs, labels=labels)
st.plotly_chart(fig3d, use_container_width=True)

# ----- Bar charts -----
st.markdown("### How each force changes plate speed and break")
plate_speeds = [t.plate_speed_mph for t in trajs]
ivbs = [t.induced_vertical_break_in for t in trajs]
horiz = [t.horizontal_break_in for t in trajs]

bar_fig = go.Figure()
bar_fig.add_trace(go.Bar(name="Plate speed (mph)", x=labels, y=plate_speeds))
bar_fig.add_trace(go.Bar(name="IVB (in)", x=labels, y=ivbs))
bar_fig.add_trace(go.Bar(name="Horiz break (in)", x=labels, y=horiz))
bar_fig.update_layout(barmode="group", height=400, legend={"orientation": "h", "y": -0.15})
st.plotly_chart(bar_fig, use_container_width=True)

st.markdown(
    f"""
    ### Reading the plot

    - **Drag bleed:** {plate_speeds[0]:.1f} mph (no drag) → {plate_speeds[1]:.1f} mph
      (with drag) = **−{plate_speeds[0] - plate_speeds[1]:.1f} mph** at the
      plate. Roughly 8 % of release speed for a typical fastball.
    - **Magnus contribution to IVB:** {ivbs[1]:+.1f} in (no Magnus) →
      {ivbs[2]:+.1f} in (with Magnus) =
      **{ivbs[2] - ivbs[1]:+.1f} in** of pure spin-induced lift.
    - At lower air density (Coors Field, hot/humid air, high altitude),
      both effects shrink. Try the env selector and watch the bars change.
    """
)
