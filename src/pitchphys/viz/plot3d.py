"""3D Plotly visualization helpers.

Plotly is imported lazily inside each function so the core package can be
used without the visualization extra installed. Use only
``plotly.graph_objects`` (no ``plotly.express``) for explicit, composable
trace control.

World-frame axes (right-handed, per :mod:`pitchphys.coordinates`):

    x = catcher's right
    y = forward toward home plate
    z = vertical, positive up

The default camera puts you behind and slightly above the catcher's left
shoulder so vertical break is visible alongside the trajectory. Aspect
mode is ``"data"`` to keep break-magnitude visually faithful.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from pitchphys.constants import DEFAULT_PLATE_DISTANCE_M
from pitchphys.coordinates import (
    STRIKE_ZONE_BOTTOM_FT,
    STRIKE_ZONE_HALF_WIDTH_FT,
    STRIKE_ZONE_TOP_FT,
)
from pitchphys.units import m_to_ft

if TYPE_CHECKING:
    import plotly.graph_objects as go

    from pitchphys.core.pitch import PitchRelease
    from pitchphys.core.trajectory import TrajectoryResult


_DEFAULT_CAMERA = {"eye": {"x": -1.4, "y": -2.0, "z": 0.6}}
_FORCE_COLORS = {
    "gravity": "tab:gray",
    "drag": "tab:orange",
    "magnus": "tab:blue",
    "non_magnus": "tab:purple",
}
# Plotly doesn't accept matplotlib "tab:*" names directly; map to hex.
_FORCE_COLORS_HEX = {
    "gravity": "#7f7f7f",
    "drag": "#ff7f0e",
    "magnus": "#1f77b4",
    "non_magnus": "#9467bd",
}
_PITCH_COLOR_CYCLE = (
    "#1f77b4",  # blue
    "#d62728",  # red
    "#2ca02c",  # green
    "#ff7f0e",  # orange
    "#9467bd",  # purple
    "#17becf",  # cyan
)


def _scale_to_units(values_m: np.ndarray, units: Literal["ft", "m"]) -> np.ndarray:
    if units == "ft":
        return np.asarray(m_to_ft(values_m))
    return np.asarray(values_m)


def _scalar_to_units(value_m: float, units: Literal["ft", "m"]) -> float:
    return float(m_to_ft(value_m)) if units == "ft" else float(value_m)


def _new_figure() -> go.Figure:
    import plotly.graph_objects as go

    fig = go.Figure()
    suffix = " (ft)"
    fig.update_layout(
        scene={
            "xaxis_title": f"x — catcher's right{suffix}",
            "yaxis_title": f"y — toward plate{suffix}",
            "zaxis_title": f"z — up{suffix}",
            "aspectmode": "data",
            "camera": _DEFAULT_CAMERA,
        },
        margin={"l": 0, "r": 0, "t": 30, "b": 0},
        legend={"orientation": "h", "y": -0.05},
    )
    return fig


def _set_axis_units(fig: go.Figure, units: Literal["ft", "m"]) -> None:
    suffix = " (ft)" if units == "ft" else " (m)"
    fig.update_layout(
        scene={
            "xaxis_title": f"x — catcher's right{suffix}",
            "yaxis_title": f"y — toward plate{suffix}",
            "zaxis_title": f"z — up{suffix}",
        },
    )


def _apply_strike_zone(fig: go.Figure, units: Literal["ft", "m"]) -> None:
    """Add a translucent strike-zone rectangle at the simulation's plate plane."""
    import plotly.graph_objects as go

    plate_y = _scalar_to_units(DEFAULT_PLATE_DISTANCE_M, units)
    if units == "ft":
        bottom = STRIKE_ZONE_BOTTOM_FT
        top = STRIKE_ZONE_TOP_FT
        half_w = STRIKE_ZONE_HALF_WIDTH_FT
    else:
        bottom = STRIKE_ZONE_BOTTOM_FT * 0.3048
        top = STRIKE_ZONE_TOP_FT * 0.3048
        half_w = STRIKE_ZONE_HALF_WIDTH_FT * 0.3048

    # Four corner vertices of the rectangle, traversed in order.
    xs = [-half_w, half_w, half_w, -half_w]
    ys = [plate_y] * 4
    zs = [bottom, bottom, top, top]
    # Mesh3d as two triangles fills the rectangle.
    fig.add_trace(
        go.Mesh3d(
            x=xs,
            y=ys,
            z=zs,
            i=[0, 0],
            j=[1, 2],
            k=[2, 3],
            color="lightgray",
            opacity=0.18,
            hoverinfo="skip",
            name="strike zone",
            showlegend=False,
        )
    )
    # Outline scatter for crisp edges.
    fig.add_trace(
        go.Scatter3d(
            x=[*xs, xs[0]],
            y=[*ys, ys[0]],
            z=[*zs, zs[0]],
            mode="lines",
            line={"color": "gray", "width": 2},
            hoverinfo="skip",
            showlegend=False,
            name="strike zone edge",
        )
    )


def trajectory_3d(
    traj: TrajectoryResult,
    *,
    fig: go.Figure | None = None,
    label: str | None = None,
    units: Literal["ft", "m"] = "ft",
    show_release: bool = True,
    show_plate: bool = True,
    show_strike_zone: bool = True,
    color: str | None = None,
    line_kwargs: dict[str, Any] | None = None,
) -> go.Figure:
    """Plot a single pitch trajectory in 3D.

    Returns the (possibly new) ``plotly.graph_objects.Figure``.
    """
    import plotly.graph_objects as go

    fig = fig if fig is not None else _new_figure()
    _set_axis_units(fig, units)
    if show_strike_zone:
        _apply_strike_zone(fig, units)

    pos = traj.position
    xs = _scale_to_units(pos[:, 0], units)
    ys = _scale_to_units(pos[:, 1], units)
    zs = _scale_to_units(pos[:, 2], units)
    line_opts: dict[str, Any] = {"width": 4}
    if color is not None:
        line_opts["color"] = color
    if line_kwargs:
        line_opts.update(line_kwargs)
    fig.add_trace(
        go.Scatter3d(
            x=xs,
            y=ys,
            z=zs,
            mode="lines",
            name=label or "trajectory",
            line=line_opts,
        )
    )
    if show_release:
        fig.add_trace(
            go.Scatter3d(
                x=[xs[0]],
                y=[ys[0]],
                z=[zs[0]],
                mode="markers",
                marker={"size": 5, "color": "black"},
                name="release",
                showlegend=False,
            )
        )
    if show_plate:
        fig.add_trace(
            go.Scatter3d(
                x=[xs[-1]],
                y=[ys[-1]],
                z=[zs[-1]],
                mode="markers",
                marker={"size": 6, "color": "red", "symbol": "x"},
                name="plate",
                showlegend=False,
            )
        )
    return fig


def compare_pitches_3d(
    trajs: Sequence[TrajectoryResult],
    *,
    labels: Sequence[str] | None = None,
    fig: go.Figure | None = None,
    units: Literal["ft", "m"] = "ft",
    show_strike_zone: bool = True,
    colors: Sequence[str] | None = None,
) -> go.Figure:
    """Overlay multiple trajectories in a single 3D scene."""
    fig = fig if fig is not None else _new_figure()
    _set_axis_units(fig, units)
    if show_strike_zone:
        _apply_strike_zone(fig, units)
    if labels is None:
        labels = [f"pitch {i + 1}" for i in range(len(trajs))]
    palette = colors if colors is not None else _PITCH_COLOR_CYCLE
    for i, (traj, label) in enumerate(zip(trajs, labels, strict=False)):
        trajectory_3d(
            traj,
            fig=fig,
            label=label,
            units=units,
            show_release=False,
            show_plate=False,
            show_strike_zone=False,
            color=palette[i % len(palette)],
        )
    return fig


def add_spin_axis_arrow(
    fig: go.Figure,
    pitch: PitchRelease,
    *,
    position: np.ndarray | None = None,
    length_ft: float = 2.0,
    color: str = "#9467bd",  # purple
    label: str = "spin axis",
    units: Literal["ft", "m"] = "ft",
) -> go.Figure:
    """Draw a 3D arrow along ``pitch.spin_axis`` at the given position."""
    import plotly.graph_objects as go

    base_m = position if position is not None else pitch.release_pos_m
    base = _scale_to_units(np.asarray(base_m, dtype=float), units)
    length_m = length_ft * 0.3048
    length_units = _scalar_to_units(length_m, units)
    direction = pitch.spin_axis  # already a unit vector
    tip = base + direction * length_units

    # Shaft
    fig.add_trace(
        go.Scatter3d(
            x=[base[0], tip[0]],
            y=[base[1], tip[1]],
            z=[base[2], tip[2]],
            mode="lines",
            line={"color": color, "width": 6},
            name=label,
            showlegend=True,
        )
    )
    # Arrowhead via Cone
    fig.add_trace(
        go.Cone(
            x=[tip[0]],
            y=[tip[1]],
            z=[tip[2]],
            u=[direction[0]],
            v=[direction[1]],
            w=[direction[2]],
            sizemode="absolute",
            sizeref=length_units * 0.25,
            colorscale=[[0, color], [1, color]],
            showscale=False,
            anchor="tip",
            hoverinfo="name",
            name=label,
            showlegend=False,
        )
    )
    return fig


def add_force_vectors(
    fig: go.Figure,
    traj: TrajectoryResult,
    *,
    times: Sequence[float] = (0.1, 0.2, 0.3),
    forces: Sequence[str] = ("gravity", "drag", "magnus"),
    scale: float = 0.05,
    units: Literal["ft", "m"] = "ft",
    colors: dict[str, str] | None = None,
) -> go.Figure:
    """Annotate the trajectory with force-vector cones at selected times.

    ``scale`` is in meters per Newton (cone tip is ``scale * |F|`` meters
    from the ball position). Default 0.05 m/N gives ~5 cm per Newton, a
    reasonable visual size for the ~1 N forces typical at MLB speeds.
    """
    import plotly.graph_objects as go

    color_map = {**_FORCE_COLORS_HEX, **(colors or {})}
    for t_target in times:
        if not len(traj.time):
            continue
        idx = int(np.argmin(np.abs(traj.time - t_target)))
        ball_pos_m = traj.position[idx]
        ball_pos = _scale_to_units(ball_pos_m, units)
        for fname in forces:
            if fname not in traj.forces:
                continue
            f_vec = traj.forces[fname][idx]
            f_mag = float(np.linalg.norm(f_vec))
            if f_mag < 1e-12:
                continue
            tip_m = ball_pos_m + f_vec * scale
            tip = _scale_to_units(tip_m, units)
            color = color_map.get(fname, "#000000")
            # Shaft
            fig.add_trace(
                go.Scatter3d(
                    x=[ball_pos[0], tip[0]],
                    y=[ball_pos[1], tip[1]],
                    z=[ball_pos[2], tip[2]],
                    mode="lines",
                    line={"color": color, "width": 4},
                    name=f"{fname} @ t={traj.time[idx]:.2f}s",
                    legendgroup=fname,
                    showlegend=False,
                )
            )
            # Arrowhead
            f_unit = f_vec / f_mag
            fig.add_trace(
                go.Cone(
                    x=[tip[0]],
                    y=[tip[1]],
                    z=[tip[2]],
                    u=[f_unit[0]],
                    v=[f_unit[1]],
                    w=[f_unit[2]],
                    sizemode="absolute",
                    sizeref=_scalar_to_units(f_mag * scale * 0.3, units),
                    colorscale=[[0, color], [1, color]],
                    showscale=False,
                    anchor="tip",
                    name=fname,
                    legendgroup=fname,
                    hoverinfo="name",
                    showlegend=False,
                )
            )
    return fig
