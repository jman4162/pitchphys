"""Smoke tests for 2D viz helpers (no rendering, just figure construction)."""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # non-interactive backend

import matplotlib.pyplot as plt

from pitchphys.core.simulate import simulate
from pitchphys.presets import curveball, four_seam
from pitchphys.viz import (
    catcher_view,
    compare_pitches,
    draw_force_arrows,
    side_view,
    top_view,
)


def _traj():
    return simulate(four_seam())


def test_side_view_returns_axes() -> None:
    fig, ax = plt.subplots()
    out = side_view(_traj(), ax=ax)
    assert out is ax
    plt.close(fig)


def test_catcher_view_returns_axes() -> None:
    fig, ax = plt.subplots()
    out = catcher_view(_traj(), ax=ax)
    assert out is ax
    plt.close(fig)


def test_top_view_returns_axes() -> None:
    fig, ax = plt.subplots()
    out = top_view(_traj(), ax=ax)
    assert out is ax
    plt.close(fig)


def test_compare_pitches_renders() -> None:
    fig, ax = plt.subplots()
    fb = simulate(four_seam())
    cb = simulate(curveball())
    compare_pitches([fb, cb], view="catcher", labels=["FB", "CB"], ax=ax)
    plt.close(fig)


def test_force_arrows_draws() -> None:
    fig, ax = plt.subplots()
    traj = _traj()
    side_view(traj, ax=ax)
    draw_force_arrows(ax, traj, times=[0.1, 0.2, 0.3], scale=0.001)
    plt.close(fig)


def test_unknown_view_raises() -> None:
    import pytest

    fig, ax = plt.subplots()
    try:
        with pytest.raises(ValueError):
            compare_pitches([_traj()], view="bogus", ax=ax)  # type: ignore[arg-type]
    finally:
        plt.close(fig)
