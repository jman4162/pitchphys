"""Basic four-seam fastball simulation.

Run with ``python examples/basic_fastball.py``.
"""

from __future__ import annotations

from pitchphys import simulate
from pitchphys.presets import four_seam


def main() -> None:
    pitch = four_seam(speed_mph=95.0, spin_rpm=2400.0, tilt_clock=12.0)
    traj = simulate(pitch)
    metrics = traj.break_metrics()
    width = max(len(k) for k in metrics)
    for k, v in metrics.items():
        print(f"{k:<{width}}  {v: .3f}")


if __name__ == "__main__":
    main()
