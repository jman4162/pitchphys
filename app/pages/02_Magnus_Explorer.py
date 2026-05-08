"""Magnus geometry explorer.

Shows the v, ω, and ω × v_hat vectors at release for a user-selected spin
configuration. Spin decay is disabled here so the drawn ω vector matches the
simulated ω throughout the flight (pedagogical clarity > fidelity).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from utils import cached_simulate, get_canonical_pitch

from pitchphys.coordinates import decompose_omega
from pitchphys.core.environment import Environment
from pitchphys.core.pitch import PitchRelease
from pitchphys.units import m_to_ft
from pitchphys.viz.plot3d import _apply_strike_zone, trajectory_3d

st.title("Magnus Effect Explorer")
st.markdown(
    """
    The Magnus force on a spinning baseball is

        F_M = ½ · ρ · C_L · A · |v|² · unit(ω × v_hat)

    The **direction** of the break is given by `ω × v_hat`. Drag the
    sliders to see how spin tilt and active fraction change the geometry.
    """
)

canonical = get_canonical_pitch()
with st.sidebar:
    st.header("Pitch")
    tilt_clock = st.slider(
        "Tilt (clock face)",
        0.0,
        12.0,
        float(canonical["tilt_clock"]),
        0.25,
        help="12:00 = backspin axis (+x). See SPEC §4.5 for the full convention.",
    )
    active_spin_fraction = st.slider(
        "Active spin fraction",
        0.0,
        1.0,
        float(canonical["active_spin_fraction"]),
        0.05,
        help="Fraction of spin perpendicular to velocity.",
    )
    throwing_hand = st.radio(
        "Throwing hand",
        ("R", "L"),
        index=0 if canonical["throwing_hand"] == "R" else 1,
        horizontal=True,
    )
    speed_mph = st.slider("Speed (mph)", 70.0, 105.0, float(canonical["speed_mph"]), 0.5)
    spin_rpm = st.slider("Spin rate (rpm)", 1500.0, 3500.0, float(canonical["spin_rpm"]), 50.0)

env = Environment.sea_level()
pitch = PitchRelease.from_mph_rpm_axis(
    speed_mph=speed_mph,
    spin_rpm=spin_rpm,
    tilt_clock=tilt_clock,
    active_spin_fraction=active_spin_fraction,
    throwing_hand=throwing_hand,
    launch_angle_deg=0.0,
    horizontal_angle_deg=0.0,
)
# Disable spin decay on this page so the rendered ω stays accurate.
traj = cached_simulate(pitch, env, spin_decay_tau_s=None)

# Geometry vectors at release
v0 = pitch.initial_velocity()
v_hat = v0 / np.linalg.norm(v0)
omega = pitch.omega_vec(v_hat)
omega_perp, _ = decompose_omega(omega, v_hat)
magnus_dir = np.cross(omega, v_hat)
magnus_dir_norm = np.linalg.norm(magnus_dir)
if magnus_dir_norm > 1e-9:
    magnus_dir = magnus_dir / magnus_dir_norm

# Build figure with trajectory only
fig = trajectory_3d(traj, label="trajectory")
fig.update_layout(
    scene_camera={"eye": {"x": 0.0, "y": -3.0, "z": 0.5}},
    height=650,
)

# ---- Add three named cones at release point ----
release_ft = m_to_ft(pitch.release_pos_m)


def _add_named_cone(
    figure: go.Figure,
    direction: np.ndarray,
    color: str,
    name: str,
    length_ft: float = 2.0,
) -> None:
    direction = direction / np.linalg.norm(direction)
    tip = release_ft + direction * length_ft
    figure.add_trace(
        go.Scatter3d(
            x=[release_ft[0], tip[0]],
            y=[release_ft[1], tip[1]],
            z=[release_ft[2], tip[2]],
            mode="lines",
            line={"color": color, "width": 8},
            name=name,
            showlegend=True,
        )
    )
    figure.add_trace(
        go.Cone(
            x=[tip[0]],
            y=[tip[1]],
            z=[tip[2]],
            u=[direction[0]],
            v=[direction[1]],
            w=[direction[2]],
            sizemode="absolute",
            sizeref=0.4,
            colorscale=[[0, color], [1, color]],
            showscale=False,
            anchor="tip",
            name=name,
            hoverinfo="name",
            showlegend=False,
        )
    )


_add_named_cone(fig, v_hat, "#d62728", "v̂ (velocity)")
_add_named_cone(fig, omega / np.linalg.norm(omega), "#1f77b4", "ω̂ (spin axis)")
if magnus_dir_norm > 1e-9:
    _add_named_cone(fig, magnus_dir, "#2ca02c", "ω × v̂  (Magnus direction)")

# Reset strike zone — already added by trajectory_3d, but layout may need refresh.
_apply_strike_zone(fig, "ft")
st.plotly_chart(fig, use_container_width=True)

# ---- Numeric panel ----
omega_perp_mag = float(np.linalg.norm(omega_perp))
omega_mag = float(np.linalg.norm(omega))
gyro_fraction = float(np.sqrt(max(0.0, 1.0 - active_spin_fraction**2)))
cols = st.columns(4)
cols[0].metric("|ω| (rad/s)", f"{omega_mag:.0f}")
cols[1].metric("|ω_perp| (rad/s)", f"{omega_perp_mag:.0f}")
cols[2].metric("Active fraction", f"{active_spin_fraction:.2f}")
cols[3].metric("Gyro fraction", f"{gyro_fraction:.2f}")

cols2 = st.columns(3)
cols2[0].metric(
    "Magnus break |x|",
    f"{traj.magnus_break_x_in:+.2f} in" if traj.grav_drag_baseline is not None else "—",
)
cols2[1].metric(
    "Magnus break |z|",
    f"{traj.magnus_break_z_in:+.2f} in" if traj.grav_drag_baseline is not None else "—",
)
cols2[2].metric("IVB", f"{traj.induced_vertical_break_in:+.2f} in")

st.markdown(
    """
    ### How to read this

    - **Red `v̂`** points toward home plate (the velocity unit vector).
    - **Blue `ω̂`** points along the spin axis (full 3D, including any gyro
      component along `v̂`).
    - **Green `ω × v̂`** is the direction the Magnus force pushes — it's
      perpendicular to both, and its magnitude is proportional to
      `|ω_perp|` (the active part of the spin).

    Try setting **active fraction = 0**: the green vector vanishes, because
    `ω` becomes parallel to `v̂` and their cross product is zero. This is
    the "pure gyro" pitch — high spin, no Magnus break.
    """
)
