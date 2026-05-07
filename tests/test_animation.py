"""Smoke tests for animated 3D figures."""

from __future__ import annotations

import pytest

pytest.importorskip("plotly")

import plotly.graph_objects as go

from pitchphys.core.simulate import simulate
from pitchphys.presets import curveball, four_seam
from pitchphys.viz.animation import animate_pitch, animate_pitches


def _traj():
    return simulate(four_seam())


def test_animate_pitch_returns_figure_with_frames() -> None:
    fig = animate_pitch(_traj())
    assert isinstance(fig, go.Figure)
    assert len(fig.frames) >= 12


def test_animate_pitch_target_frames_override() -> None:
    fig = animate_pitch(_traj(), target_frames=8)
    assert len(fig.frames) == 8


def test_animate_pitch_first_and_last_frame_endpoints() -> None:
    traj = _traj()
    fig = animate_pitch(traj, target_frames=20)
    # First frame data[0] is the ball at release.
    first_ball = fig.frames[0].data[0]
    last_ball = fig.frames[-1].data[0]
    # Convert release position to ft (the default units).
    import numpy as np

    from pitchphys.units import m_to_ft

    expected_release = m_to_ft(traj.position[0])
    expected_plate = m_to_ft(traj.position[-1])
    np.testing.assert_allclose(
        [first_ball.x[0], first_ball.y[0], first_ball.z[0]],
        expected_release,
        atol=1e-6,
    )
    np.testing.assert_allclose(
        [last_ball.x[0], last_ball.y[0], last_ball.z[0]],
        expected_plate,
        atol=1e-6,
    )


def test_animate_pitch_has_play_button_and_slider() -> None:
    fig = animate_pitch(_traj(), target_frames=15)
    menus = fig.layout.updatemenus or ()
    sliders = fig.layout.sliders or ()
    assert len(menus) >= 1
    assert len(sliders) >= 1
    button_labels = [b.label for b in menus[0].buttons]
    assert any("Play" in (lbl or "") for lbl in button_labels)


def test_animate_pitches_synchronized() -> None:
    fb = simulate(four_seam())
    cb = simulate(curveball())
    fig = animate_pitches([fb, cb], labels=["FB", "CB"], target_frames=20)
    assert len(fig.frames) == 20
    # Each frame contains 2 pitches × (ball + trail) = 4 trace updates.
    assert len(fig.frames[0].data) == 4


def test_animate_pitches_requires_nonempty() -> None:
    with pytest.raises(ValueError):
        animate_pitches([])


def test_animate_pitch_show_trail_off_omits_trail_traces() -> None:
    fig_with = animate_pitch(_traj(), target_frames=10, show_trail=True)
    fig_without = animate_pitch(_traj(), target_frames=10, show_trail=False)
    # Each trail-on frame has 2 trace updates (ball + trail); trail-off has 1.
    assert len(fig_with.frames[0].data) == 2
    assert len(fig_without.frames[0].data) == 1
