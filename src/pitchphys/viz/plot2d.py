"""2D Matplotlib visualization helpers.

Matplotlib is imported lazily inside each function so the core package can be
used without the visualization extra installed.

All views default to feet on both axes; pass ``units="m"`` to switch.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from typing import TYPE_CHECKING, Any, Literal

import numpy as np

from pitchphys.coordinates import (
    STRIKE_ZONE_BOTTOM_FT,
    STRIKE_ZONE_HALF_WIDTH_FT,
    STRIKE_ZONE_TOP_FT,
)
from pitchphys.units import m_to_ft

if TYPE_CHECKING:
    from matplotlib.axes import Axes

    from pitchphys.core.trajectory import TrajectoryResult


ViewName = Literal["side", "catcher", "top"]


def _xy_for_view(
    traj: TrajectoryResult, view: ViewName, units: Literal["ft", "m"]
) -> tuple[np.ndarray, np.ndarray, str, str]:
    """Pick the (x, y) arrays and axis labels for a given view."""
    pos = traj.position
    if view == "side":
        x = pos[:, 1]  # forward
        y = pos[:, 2]  # up
        xl, yl = "y (forward)", "z (up)"
    elif view == "catcher":
        x = pos[:, 0]  # right
        y = pos[:, 2]  # up
        xl, yl = "x (catcher's right)", "z (up)"
    elif view == "top":
        x = pos[:, 1]  # forward
        y = pos[:, 0]  # right
        xl, yl = "y (forward)", "x (catcher's right)"
    else:
        raise ValueError(f"Unknown view {view!r}; expected 'side', 'catcher', or 'top'.")
    if units == "ft":
        x = m_to_ft(x)
        y = m_to_ft(y)
        xl += " (ft)"
        yl += " (ft)"
    else:
        xl += " (m)"
        yl += " (m)"
    return np.asarray(x), np.asarray(y), xl, yl


def _setup_axes(ax: Axes | None) -> Axes:
    import matplotlib.pyplot as plt

    if ax is None:
        _, ax = plt.subplots()
    return ax


def _draw_strike_zone(ax: Axes, units: Literal["ft", "m"]) -> None:
    import matplotlib.patches as patches

    if units == "ft":
        bottom = STRIKE_ZONE_BOTTOM_FT
        top = STRIKE_ZONE_TOP_FT
        half_w = STRIKE_ZONE_HALF_WIDTH_FT
    else:
        bottom = STRIKE_ZONE_BOTTOM_FT * 0.3048
        top = STRIKE_ZONE_TOP_FT * 0.3048
        half_w = STRIKE_ZONE_HALF_WIDTH_FT * 0.3048
    rect = patches.Rectangle(
        (-half_w, bottom),
        2 * half_w,
        top - bottom,
        linewidth=1.0,
        edgecolor="black",
        facecolor="none",
        linestyle="--",
    )
    ax.add_patch(rect)


def side_view(
    traj: TrajectoryResult,
    ax: Axes | None = None,
    units: Literal["ft", "m"] = "ft",
    show_release: bool = True,
    show_plate: bool = True,
    label: str | None = None,
    **kwargs: Any,
) -> Axes:
    """Plot the trajectory from the side (y vs. z)."""
    ax = _setup_axes(ax)
    x, y, xl, yl = _xy_for_view(traj, "side", units)
    ax.plot(x, y, label=label, **kwargs)
    if show_release:
        ax.plot([x[0]], [y[0]], "o", color="black", markersize=4)
    if show_plate:
        ax.plot([x[-1]], [y[-1]], "x", color="red", markersize=8)
    ax.set_xlabel(xl)
    ax.set_ylabel(yl)
    return ax


def catcher_view(
    traj: TrajectoryResult,
    ax: Axes | None = None,
    units: Literal["ft", "m"] = "ft",
    show_strike_zone: bool = True,
    show_trajectory: bool = True,
    label: str | None = None,
    **kwargs: Any,
) -> Axes:
    """Plot the trajectory as seen by the catcher (x vs. z)."""
    ax = _setup_axes(ax)
    x, y, xl, yl = _xy_for_view(traj, "catcher", units)
    if show_trajectory:
        ax.plot(x, y, label=label, alpha=0.7, **kwargs)
    ax.plot([x[-1]], [y[-1]], "o", markersize=6, **kwargs)
    if show_strike_zone:
        _draw_strike_zone(ax, units)
    ax.set_xlabel(xl)
    ax.set_ylabel(yl)
    ax.set_aspect("equal")
    return ax


def top_view(
    traj: TrajectoryResult,
    ax: Axes | None = None,
    units: Literal["ft", "m"] = "ft",
    label: str | None = None,
    **kwargs: Any,
) -> Axes:
    """Plot the trajectory from above (y vs. x)."""
    ax = _setup_axes(ax)
    x, y, xl, yl = _xy_for_view(traj, "top", units)
    ax.plot(x, y, label=label, **kwargs)
    ax.set_xlabel(xl)
    ax.set_ylabel(yl)
    return ax


def compare_pitches(
    trajs: Sequence[TrajectoryResult],
    view: ViewName = "catcher",
    labels: Sequence[str] | None = None,
    ax: Axes | None = None,
    units: Literal["ft", "m"] = "ft",
    **kwargs: Any,
) -> Axes:
    """Overlay multiple trajectories on a shared view."""
    ax = _setup_axes(ax)
    if labels is None:
        labels = [f"pitch {i}" for i in range(len(trajs))]
    for traj, lab in zip(trajs, labels, strict=False):
        if view == "side":
            side_view(traj, ax=ax, units=units, label=lab, **kwargs)
        elif view == "catcher":
            catcher_view(traj, ax=ax, units=units, label=lab, **kwargs)
        elif view == "top":
            top_view(traj, ax=ax, units=units, label=lab, **kwargs)
        else:
            raise ValueError(f"Unknown view {view!r}")
    ax.legend()
    return ax


def draw_force_arrows(
    ax: Axes,
    traj: TrajectoryResult,
    times: Iterable[float],
    scale: float = 1.0,
    view: ViewName = "side",
    units: Literal["ft", "m"] = "ft",
) -> None:
    """Annotate force vectors at selected times on an existing axis."""
    forces_to_draw = ["gravity", "drag", "magnus"]
    colors = {"gravity": "tab:gray", "drag": "tab:orange", "magnus": "tab:blue"}
    pos_xy_x, pos_xy_y, _, _ = _xy_for_view(traj, view, units)

    for t_target in times:
        i = int(np.argmin(np.abs(traj.time - t_target)))
        for fname in forces_to_draw:
            if fname not in traj.forces:
                continue
            f_vec = traj.forces[fname][i]
            if view == "side":
                fx, fy = f_vec[1], f_vec[2]
            elif view == "catcher":
                fx, fy = f_vec[0], f_vec[2]
            else:  # top
                fx, fy = f_vec[1], f_vec[0]
            ax.annotate(
                "",
                xy=(pos_xy_x[i] + fx * scale, pos_xy_y[i] + fy * scale),
                xytext=(pos_xy_x[i], pos_xy_y[i]),
                arrowprops={"arrowstyle": "->", "color": colors.get(fname, "black")},
            )
