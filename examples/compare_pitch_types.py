"""Compare pitch types from the catcher's view.

Run with ``python examples/compare_pitch_types.py``. Shows a 2D plot with
overlaid trajectories from the four_seam, curveball, slider, sinker, and
changeup presets.
"""

from __future__ import annotations

import matplotlib

matplotlib.use("Agg")  # non-interactive backend; no Tk required

import matplotlib.pyplot as plt

from pitchphys import simulate
from pitchphys.presets import changeup, curveball, four_seam, sinker, slider
from pitchphys.viz import compare_pitches


def main() -> None:
    pitches = {
        "four-seam": four_seam(),
        "curveball": curveball(),
        "slider": slider(),
        "sinker": sinker(),
        "changeup": changeup(),
    }
    trajs = [simulate(p) for p in pitches.values()]

    _fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    compare_pitches(trajs, view="catcher", labels=list(pitches), ax=axes[0])
    axes[0].set_title("Catcher view (x vs z, ft)")
    compare_pitches(trajs, view="side", labels=list(pitches), ax=axes[1])
    axes[1].set_title("Side view (y vs z, ft)")

    print(f"{'pitch':<12} {'plate_speed':>12} {'IVB_in':>8} {'horiz_in':>8}")
    for name, traj in zip(pitches, trajs, strict=False):
        print(
            f"{name:<12} {traj.plate_speed_mph:>11.1f}  "
            f"{traj.induced_vertical_break_in:>+7.2f}  "
            f"{traj.horizontal_break_in:>+7.2f}"
        )

    plt.tight_layout()
    out_path = "examples/compare_pitch_types.png"
    plt.savefig(out_path, dpi=120)
    print(f"\nSaved figure to {out_path}")


if __name__ == "__main__":
    main()
