"""Animated 3D trajectory using Plotly frames + slider/play.

Plotly figure ``frames`` together with ``updatemenus`` and ``sliders``
provide a play/pause/scrub experience entirely in the browser. We don't
require a server callback. Frame durations below ~30 ms tend to stutter
in browsers; default is 30 fps which gives 33 ms per frame.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Literal

import numpy as np

from pitchphys.viz.plot3d import (
    _PITCH_COLOR_CYCLE,
    _apply_strike_zone,
    _new_figure,
    _scale_to_units,
    _set_axis_units,
)

if TYPE_CHECKING:
    import plotly.graph_objects as go

    from pitchphys.core.trajectory import TrajectoryResult


def _resample_trajectory(traj: TrajectoryResult, n_frames: int) -> tuple[np.ndarray, np.ndarray]:
    """Linear-interpolate position to ``n_frames`` uniform samples in time."""
    t_uniform = np.linspace(0.0, float(traj.time[-1]), n_frames)
    pos = np.empty((n_frames, 3))
    for axis in range(3):
        pos[:, axis] = np.interp(t_uniform, traj.time, traj.position[:, axis])
    return t_uniform, pos


def _frame_count(traj: TrajectoryResult, fps: int, target_frames: int | None) -> int:
    if target_frames is not None:
        return max(2, int(target_frames))
    return max(12, round(traj.flight_time_s * fps))


def animate_pitch(
    traj: TrajectoryResult,
    *,
    fps: int = 30,
    fig: go.Figure | None = None,
    units: Literal["ft", "m"] = "ft",
    show_trail: bool = True,
    show_strike_zone: bool = True,
    target_frames: int | None = None,
) -> go.Figure:
    """Build an animated 3D figure for a single pitch trajectory.

    The figure has a Play button and a frame slider. ``target_frames``
    overrides the auto frame count derived from ``fps * flight_time``.
    """
    import plotly.graph_objects as go

    fig = fig if fig is not None else _new_figure()
    _set_axis_units(fig, units)
    if show_strike_zone:
        _apply_strike_zone(fig, units)

    n = _frame_count(traj, fps, target_frames)
    t_uniform, pos_m = _resample_trajectory(traj, n)
    pos = np.column_stack([_scale_to_units(pos_m[:, axis], units) for axis in range(3)])

    # Static traces: full path (faint reference) + initial ball + initial trail.
    fig.add_trace(
        go.Scatter3d(
            x=pos[:, 0],
            y=pos[:, 1],
            z=pos[:, 2],
            mode="lines",
            line={"color": "rgba(31,119,180,0.25)", "width": 2},
            name="full path",
            showlegend=False,
            hoverinfo="skip",
        )
    )
    ball_trace_index = len(fig.data)
    fig.add_trace(
        go.Scatter3d(
            x=[pos[0, 0]],
            y=[pos[0, 1]],
            z=[pos[0, 2]],
            mode="markers",
            marker={"size": 7, "color": "#1f77b4"},
            name="ball",
            showlegend=False,
        )
    )
    trail_trace_index = len(fig.data)
    if show_trail:
        fig.add_trace(
            go.Scatter3d(
                x=pos[:1, 0],
                y=pos[:1, 1],
                z=pos[:1, 2],
                mode="lines",
                line={"color": "#1f77b4", "width": 5},
                name="trail",
                showlegend=False,
            )
        )

    # Frames update only the ball + trail traces, identified by index.
    frames = []
    for i in range(n):
        ball = go.Scatter3d(
            x=[pos[i, 0]],
            y=[pos[i, 1]],
            z=[pos[i, 2]],
            mode="markers",
            marker={"size": 7, "color": "#1f77b4"},
        )
        if show_trail:
            trail = go.Scatter3d(
                x=pos[: i + 1, 0],
                y=pos[: i + 1, 1],
                z=pos[: i + 1, 2],
                mode="lines",
                line={"color": "#1f77b4", "width": 5},
            )
            data = [ball, trail]
            traces = [ball_trace_index, trail_trace_index]
        else:
            data = [ball]
            traces = [ball_trace_index]
        frames.append(
            go.Frame(
                data=data,
                traces=traces,
                name=f"f{i}",
            )
        )
    fig.frames = frames

    duration_ms = max(16, round(1000.0 / fps))
    fig.update_layout(
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "buttons": [
                    {
                        "label": "▶ Play",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {"duration": duration_ms, "redraw": True},
                                "fromcurrent": True,
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                    {
                        "label": "⏸ Pause",
                        "method": "animate",
                        "args": [
                            [None],
                            {
                                "frame": {"duration": 0, "redraw": False},
                                "mode": "immediate",
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                ],
                "x": 0.0,
                "xanchor": "left",
                "y": 1.05,
                "yanchor": "top",
            }
        ],
        sliders=[
            {
                "active": 0,
                "currentvalue": {"prefix": "t = ", "suffix": " s"},
                "steps": [
                    {
                        "method": "animate",
                        "args": [
                            [f"f{i}"],
                            {
                                "frame": {"duration": 0, "redraw": True},
                                "mode": "immediate",
                                "transition": {"duration": 0},
                            },
                        ],
                        "label": f"{t_uniform[i]:.3f}",
                    }
                    for i in range(n)
                ],
                "x": 0.0,
                "xanchor": "left",
                "y": -0.05,
                "yanchor": "top",
                "len": 1.0,
            }
        ],
    )
    return fig


def animate_pitches(
    trajs: Sequence[TrajectoryResult],
    *,
    labels: Sequence[str] | None = None,
    fps: int = 30,
    fig: go.Figure | None = None,
    units: Literal["ft", "m"] = "ft",
    target_frames: int | None = None,
) -> go.Figure:
    """Animate multiple pitches synchronized on a shared time grid.

    Each pitch gets a colored ball + trail. All balls advance together over
    a common normalized time index; pitches with shorter flight reach the
    plate sooner and freeze at the plate position for remaining frames.
    """
    import plotly.graph_objects as go

    if not trajs:
        raise ValueError("animate_pitches requires at least one trajectory")
    fig = fig if fig is not None else _new_figure()
    _set_axis_units(fig, units)
    _apply_strike_zone(fig, units)

    if labels is None:
        labels = [f"pitch {i + 1}" for i in range(len(trajs))]
    palette = _PITCH_COLOR_CYCLE

    # Use the longest flight time so all pitches have data for every frame
    # (shorter pitches "land" at the plate and stay there).
    longest_flight = max(t.flight_time_s for t in trajs)
    n = (
        max(2, int(target_frames))
        if target_frames is not None
        else max(12, round(longest_flight * fps))
    )

    # Resample each trajectory to a common t_uniform on [0, longest_flight].
    t_uniform = np.linspace(0.0, longest_flight, n)
    resampled: list[np.ndarray] = []
    for traj in trajs:
        pos = np.empty((n, 3))
        clamp_t = np.clip(t_uniform, 0.0, traj.time[-1])
        for axis in range(3):
            pos[:, axis] = np.interp(clamp_t, traj.time, traj.position[:, axis])
        pos = np.column_stack([_scale_to_units(pos[:, axis], units) for axis in range(3)])
        resampled.append(pos)

    # Static path + initial ball/trail per pitch.
    ball_indices: list[int] = []
    trail_indices: list[int] = []
    for i, (pos, label) in enumerate(zip(resampled, labels, strict=False)):
        color = palette[i % len(palette)]
        fig.add_trace(
            go.Scatter3d(
                x=pos[:, 0],
                y=pos[:, 1],
                z=pos[:, 2],
                mode="lines",
                line={"color": color, "width": 2},
                opacity=0.25,
                name=label,
                showlegend=True,
                hoverinfo="skip",
            )
        )
        ball_indices.append(len(fig.data))
        fig.add_trace(
            go.Scatter3d(
                x=[pos[0, 0]],
                y=[pos[0, 1]],
                z=[pos[0, 2]],
                mode="markers",
                marker={"size": 7, "color": color},
                name=f"{label} ball",
                showlegend=False,
            )
        )
        trail_indices.append(len(fig.data))
        fig.add_trace(
            go.Scatter3d(
                x=pos[:1, 0],
                y=pos[:1, 1],
                z=pos[:1, 2],
                mode="lines",
                line={"color": color, "width": 5},
                name=f"{label} trail",
                showlegend=False,
            )
        )

    # Frames update all balls + trails per pitch.
    frames = []
    for fi in range(n):
        data = []
        traces = []
        for pi, pos in enumerate(resampled):
            ball = go.Scatter3d(
                x=[pos[fi, 0]],
                y=[pos[fi, 1]],
                z=[pos[fi, 2]],
                mode="markers",
                marker={"size": 7, "color": palette[pi % len(palette)]},
            )
            trail = go.Scatter3d(
                x=pos[: fi + 1, 0],
                y=pos[: fi + 1, 1],
                z=pos[: fi + 1, 2],
                mode="lines",
                line={"color": palette[pi % len(palette)], "width": 5},
            )
            data.extend([ball, trail])
            traces.extend([ball_indices[pi], trail_indices[pi]])
        frames.append(go.Frame(data=data, traces=traces, name=f"f{fi}"))
    fig.frames = frames

    duration_ms = max(16, round(1000.0 / fps))
    fig.update_layout(
        updatemenus=[
            {
                "type": "buttons",
                "showactive": False,
                "buttons": [
                    {
                        "label": "▶ Play",
                        "method": "animate",
                        "args": [
                            None,
                            {
                                "frame": {"duration": duration_ms, "redraw": True},
                                "fromcurrent": True,
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                    {
                        "label": "⏸ Pause",
                        "method": "animate",
                        "args": [
                            [None],
                            {
                                "frame": {"duration": 0, "redraw": False},
                                "mode": "immediate",
                                "transition": {"duration": 0},
                            },
                        ],
                    },
                ],
                "x": 0.0,
                "xanchor": "left",
                "y": 1.05,
                "yanchor": "top",
            }
        ],
        sliders=[
            {
                "active": 0,
                "currentvalue": {"prefix": "t = ", "suffix": " s"},
                "steps": [
                    {
                        "method": "animate",
                        "args": [
                            [f"f{i}"],
                            {
                                "frame": {"duration": 0, "redraw": True},
                                "mode": "immediate",
                                "transition": {"duration": 0},
                            },
                        ],
                        "label": f"{t_uniform[i]:.3f}",
                    }
                    for i in range(n)
                ],
                "x": 0.0,
                "xanchor": "left",
                "y": -0.05,
                "yanchor": "top",
                "len": 1.0,
            }
        ],
    )
    return fig
