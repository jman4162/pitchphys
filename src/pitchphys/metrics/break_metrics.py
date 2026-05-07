"""Functional access to break metrics on a TrajectoryResult."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pitchphys.core.trajectory import TrajectoryResult


def break_metrics(traj: TrajectoryResult) -> dict[str, float]:
    """Return all SPEC §11 break metrics from a trajectory.

    Equivalent to ``traj.break_metrics()`` — provided as a free function for
    use in functional pipelines.
    """
    return traj.break_metrics()
