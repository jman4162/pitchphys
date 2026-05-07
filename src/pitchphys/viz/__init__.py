"""2D and 3D visualization helpers (matplotlib + plotly lazy-imported)."""

from pitchphys.viz.animation import animate_pitch, animate_pitches
from pitchphys.viz.plot2d import (
    catcher_view,
    compare_pitches,
    draw_force_arrows,
    side_view,
    top_view,
)
from pitchphys.viz.plot3d import (
    add_force_vectors,
    add_spin_axis_arrow,
    compare_pitches_3d,
    trajectory_3d,
)

__all__ = [
    "add_force_vectors",
    "add_spin_axis_arrow",
    "animate_pitch",
    "animate_pitches",
    "catcher_view",
    "compare_pitches",
    "compare_pitches_3d",
    "draw_force_arrows",
    "side_view",
    "top_view",
    "trajectory_3d",
]
