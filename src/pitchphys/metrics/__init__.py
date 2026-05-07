"""Pitch break metrics.

In v0.1 the break metrics are exposed as properties on
:class:`pitchphys.core.trajectory.TrajectoryResult`. This module re-exports
``break_metrics`` for users who prefer a functional API.
"""

from pitchphys.metrics.break_metrics import break_metrics

__all__ = ["break_metrics"]
