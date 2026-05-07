"""Smoke tests for 3D Plotly viz helpers."""

from __future__ import annotations

import pytest

pytest.importorskip("plotly")

import plotly.graph_objects as go

from pitchphys.core.simulate import simulate
from pitchphys.presets import curveball, four_seam
from pitchphys.viz.plot3d import (
    add_force_vectors,
    add_spin_axis_arrow,
    compare_pitches_3d,
    trajectory_3d,
)


def _traj():
    return simulate(four_seam())


def test_trajectory_3d_returns_figure() -> None:
    fig = trajectory_3d(_traj())
    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 1


def test_trajectory_3d_no_strike_zone() -> None:
    fig = trajectory_3d(_traj(), show_strike_zone=False)
    n_with = len(trajectory_3d(_traj(), show_strike_zone=True).data)
    assert len(fig.data) < n_with


def test_compare_pitches_3d_has_one_line_trace_per_pitch() -> None:
    fb = simulate(four_seam())
    cb = simulate(curveball())
    fig = compare_pitches_3d([fb, cb], labels=["FB", "CB"])
    line_traces = [
        t
        for t in fig.data
        if isinstance(t, go.Scatter3d) and t.mode == "lines" and t.name in {"FB", "CB"}
    ]
    assert len(line_traces) == 2


def test_add_spin_axis_arrow_adds_traces() -> None:
    fig = trajectory_3d(_traj())
    n_before = len(fig.data)
    add_spin_axis_arrow(fig, _traj().pitch)
    # Adds a shaft (Scatter3d) + arrowhead (Cone) = 2 traces.
    assert len(fig.data) - n_before == 2


def test_add_force_vectors_per_time_per_force() -> None:
    traj = _traj()
    fig = trajectory_3d(traj)
    n_before = len(fig.data)
    add_force_vectors(
        fig,
        traj,
        times=(0.1, 0.2),
        forces=("gravity", "drag", "magnus"),
    )
    # 2 times × 3 forces × (shaft + cone) = 12 traces
    added = len(fig.data) - n_before
    assert added == 12


def test_add_force_vectors_skips_missing_force_name() -> None:
    traj = _traj()
    fig = trajectory_3d(traj)
    n_before = len(fig.data)
    add_force_vectors(fig, traj, times=(0.1,), forces=("gravity", "nonexistent"))
    # Only gravity contributes: 1 shaft + 1 cone = 2.
    assert len(fig.data) - n_before == 2


def test_strike_zone_outline_present() -> None:
    fig = trajectory_3d(_traj(), show_strike_zone=True)
    names = [getattr(t, "name", "") or "" for t in fig.data]
    assert any("strike zone" in n for n in names)


def test_units_meters_changes_axis_titles() -> None:
    fig_ft = trajectory_3d(_traj(), units="ft")
    fig_m = trajectory_3d(_traj(), units="m")
    assert "(ft)" in fig_ft.layout.scene.xaxis.title.text
    assert "(m)" in fig_m.layout.scene.xaxis.title.text
