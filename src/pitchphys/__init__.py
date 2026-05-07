"""pitchphys — educational baseball-pitch trajectory simulator.

Quickstart::

    from pitchphys import simulate
    from pitchphys.presets import four_seam

    traj = simulate(four_seam(speed_mph=95, spin_rpm=2400))
    print(traj.break_metrics())

See ``SPEC_DRAFT.md`` for the full design and ``CLAUDE.md`` for the
architectural contract.
"""

from pitchphys import presets, units
from pitchphys.core import (
    Baseball,
    Environment,
    PitchRelease,
    TrajectoryResult,
    simulate,
    simulate_many,
)

__version__ = "0.1.0"

__all__ = [
    "Baseball",
    "Environment",
    "PitchRelease",
    "TrajectoryResult",
    "presets",
    "simulate",
    "simulate_many",
    "units",
]
