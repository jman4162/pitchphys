"""Build the 3 v0.2 educational notebooks via nbformat.

Run from the repo root:

    .venv/bin/python scripts/build_notebooks.py

Outputs:
    notebooks/03_magnus_effect_fastball_curveball.ipynb
    notebooks/05_active_spin_vs_gyro_spin.ipynb
    notebooks/09_build_your_own_pitch.ipynb
"""

from __future__ import annotations

from pathlib import Path

import nbformat as nbf
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

OUT_DIR = Path(__file__).resolve().parents[1] / "notebooks"
OUT_DIR.mkdir(exist_ok=True)

# GitHub coordinates used to construct Colab links.
REPO_SLUG = "jman4162/pitchphys"
BRANCH = "main"


def md(text: str):
    return new_markdown_cell(text)


def code(text: str):
    return new_code_cell(text)


def _colab_badge(notebook_name: str) -> str:
    """Markdown for an 'Open in Colab' badge linking to the notebook on GitHub."""
    url = (
        f"https://colab.research.google.com/github/{REPO_SLUG}/blob/{BRANCH}/"
        f"notebooks/{notebook_name}"
    )
    return f"[![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)]({url})"


def with_colab_badge(intro_md: str, notebook_name: str) -> str:
    """Insert the Colab badge right after the H1 title in an intro cell."""
    badge = _colab_badge(notebook_name)
    if "\n\n" in intro_md:
        title, body = intro_md.split("\n\n", 1)
        return f"{title}\n\n{badge}\n\n{body}"
    return f"{badge}\n\n{intro_md}"


COLAB_INSTALL_CODE = (
    "# Auto-install pitchphys when running on Colab.\n"
    "import sys\n"
    "\n"
    'if "google.colab" in sys.modules:\n'
    f'    !pip install -q "pitchphys[viz] @ git+https://github.com/{REPO_SLUG}.git"\n'
    "\n"
    "import pitchphys\n"
    'print(f"pitchphys {pitchphys.__version__}")'
)


# ---------------------------------------------------------------------------
# Notebook 03: Magnus effect — fastball vs curveball
# ---------------------------------------------------------------------------

nb03 = new_notebook(
    cells=[
        md(
            "# 03 — Magnus effect: fastball vs curveball\n\n"
            "Why does a 4-seam fastball seem to *rise*, while a curveball drops "
            "more than gravity alone would explain? The answer is the Magnus force, "
            "and the only difference between the two pitches in this notebook is "
            "the direction of the spin axis. Everything else (drag, gravity, "
            "atmosphere) is identical.\n\n"
            "We'll simulate both pitches, plot their trajectories from multiple "
            "angles, and decompose the forces over time.\n\n"
            "Reference: SPEC §4.1 'A fastball does not rise; it drops less.'"
        ),
        code(
            "import numpy as np\n"
            "import matplotlib.pyplot as plt\n\n"
            "from pitchphys import simulate\n"
            "from pitchphys.presets import four_seam, curveball\n"
            "from pitchphys.viz.plot2d import compare_pitches\n"
            "from pitchphys.viz.plot3d import compare_pitches_3d"
        ),
        md(
            "## 1. Build the two pitches\n\n"
            "A 95 mph 12:00-tilt 4-seamer (pure backspin) versus an 80 mph 6:00-tilt "
            "curveball (pure topspin). Defaults match the league archetypes."
        ),
        code(
            "fb = four_seam(speed_mph=95, spin_rpm=2400, tilt_clock=12.0)\n"
            "cb = curveball(speed_mph=80, spin_rpm=2700, tilt_clock=6.0)\n"
            "fb, cb"
        ),
        md("## 2. Simulate"),
        code(
            "traj_fb = simulate(fb)\n"
            "traj_cb = simulate(cb)\n"
            "for label, traj in [('Fastball', traj_fb), ('Curveball', traj_cb)]:\n"
            "    print(f'{label:<10} '\n"
            "          f'release {traj.release_speed_mph:.1f} mph -> '\n"
            "          f'plate {traj.plate_speed_mph:.1f} mph, '\n"
            "          f'IVB {traj.induced_vertical_break_in:+.1f} in, '\n"
            "          f'flight {traj.flight_time_s:.2f} s')"
        ),
        md(
            "Notice the IVB signs. Positive IVB means the pitch ends up *above* a "
            "no-force projectile launched with the same release velocity — i.e., "
            "the Magnus force lifted the ball. Negative IVB means the Magnus force "
            "pushed it down beyond gravity's drop."
        ),
        md("## 3. Catcher view + side view"),
        code(
            "fig, axes = plt.subplots(1, 2, figsize=(11, 4))\n"
            "compare_pitches([traj_fb, traj_cb], view='catcher', labels=['FB', 'CB'], ax=axes[0])\n"
            "axes[0].set_title('Catcher view')\n"
            "compare_pitches([traj_fb, traj_cb], view='side', labels=['FB', 'CB'], ax=axes[1])\n"
            "axes[1].set_title('Side view')\n"
            "fig.tight_layout()\n"
            "plt.show()"
        ),
        md(
            "From the catcher's view both pitches end near the strike zone, but the "
            "side view shows the dramatic difference: the fastball is ~20 in. higher "
            "at the plate than the curveball, despite being released from the same "
            "height. That ~20 in. is the difference Magnus makes."
        ),
        md("## 4. Interactive 3D"),
        code(
            "fig3d = compare_pitches_3d([traj_fb, traj_cb], labels=['Fastball', 'Curveball'])\n"
            "fig3d.show()"
        ),
        md("## 5. Force magnitudes over time"),
        code(
            "fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)\n"
            "pairs = [('Fastball', traj_fb), ('Curveball', traj_cb)]\n"
            "for ax, (name, traj) in zip(axes, pairs, strict=False):\n"
            "    for fname, color in [('gravity', 'tab:gray'), ('drag', 'tab:orange'), ('magnus', 'tab:blue')]:\n"
            "        mag = np.linalg.norm(traj.forces[fname], axis=1)\n"
            "        ax.plot(traj.time, mag, label=fname, color=color)\n"
            "    ax.set_title(name)\n"
            "    ax.set_xlabel('t (s)')\n"
            "    ax.set_ylabel('|F| (N)')\n"
            "    ax.legend()\n"
            "    ax.grid(True, alpha=0.3)\n"
            "fig.tight_layout()\n"
            "plt.show()"
        ),
        md(
            "Gravity is constant at `m·g ≈ 1.42 N` throughout. Drag and Magnus "
            "scale with `|v|^2`, so they decline as the pitch slows. The fastball "
            "shows a larger Magnus force (positive sign perpendicular to velocity, "
            "lifting the ball); the curveball's Magnus force is similar in magnitude "
            "but oriented downward.\n\n"
            "## Takeaway\n\n"
            "The fastball never literally *rises*. Gravity always pulls it down. But "
            "the Magnus force counteracts a portion of gravity's drop, so the ball "
            "ends up ~20 in. higher than a spinless equivalent — enough to look like "
            "a 'rise' to the hitter. The curveball does the opposite: Magnus and "
            "gravity work *together*, and the ball drops dramatically."
        ),
    ]
)

# ---------------------------------------------------------------------------
# Notebook 05: Active vs gyro spin
# ---------------------------------------------------------------------------

nb05 = new_notebook(
    cells=[
        md(
            "# 05 — Active spin vs gyro spin\n\n"
            "Spin rate alone does not determine pitch movement. The *direction* of "
            "the spin axis matters: only the component of `ω` perpendicular to "
            "velocity contributes to the Magnus force. The parallel component (gyro "
            "spin) doesn't move the ball.\n\n"
            "This notebook holds total spin constant at 2,500 rpm and sweeps the "
            "active-spin fraction from 0 to 1, showing how break collapses as the "
            "pitch becomes more 'gyro-like'.\n\n"
            "Reference: SPEC §4.4 — 'Spin rate is not movement.'"
        ),
        code(
            "import numpy as np\n"
            "import pandas as pd\n"
            "import matplotlib.pyplot as plt\n\n"
            "from pitchphys import simulate\n"
            "from pitchphys.core.pitch import PitchRelease\n"
            "from pitchphys.viz.plot3d import compare_pitches_3d"
        ),
        md(
            "## 1. Sweep active fraction\n\n"
            "21 samples from 0 (pure gyro) to 1 (pure active spin). Total spin and "
            "tilt are held constant."
        ),
        code(
            "fractions = np.linspace(0.0, 1.0, 21)\n"
            "rows = []\n"
            "trajs = []\n"
            "for a in fractions:\n"
            "    pitch = PitchRelease.from_mph_rpm_axis(\n"
            "        speed_mph=92.0, spin_rpm=2500.0, tilt_clock=12.0,\n"
            "        active_spin_fraction=float(a),\n"
            "    )\n"
            "    traj = simulate(pitch)\n"
            "    trajs.append(traj)\n"
            "    rows.append({\n"
            "        'active_fraction': a,\n"
            "        'IVB_in': traj.induced_vertical_break_in,\n"
            "        'horizontal_break_in': traj.horizontal_break_in,\n"
            "        'magnus_break_magnitude_in': traj.magnus_break_magnitude_in,\n"
            "    })\n"
            "df = pd.DataFrame(rows)\n"
            "df.head()"
        ),
        md("## 2. Plot the sweep"),
        code(
            "fig, ax = plt.subplots(figsize=(8, 4.5))\n"
            "ax.plot(df['active_fraction'], df['magnus_break_magnitude_in'], 'o-', label='Magnus |break|')\n"
            "ax.plot(df['active_fraction'], df['IVB_in'], 's--', label='IVB')\n"
            "ax.plot(df['active_fraction'], df['horizontal_break_in'], '^:', label='Horiz break')\n"
            "ax.set_xlabel('Active spin fraction')\n"
            "ax.set_ylabel('Break (in)')\n"
            "ax.set_title('Total spin = 2,500 rpm; only active fraction is changing')\n"
            "ax.legend()\n"
            "ax.grid(True, alpha=0.3)\n"
            "plt.show()"
        ),
        md(
            "At fraction 0, the spin axis is fully aligned with velocity — there's "
            "no perpendicular component, so Magnus break is essentially zero. As the "
            "active fraction rises toward 1, the full Magnus break is realized.\n\n"
            "**The takeaway**: a 2,500 rpm gyro slider has the same total spin as a "
            "2,500 rpm 4-seam fastball — and yet the slider has roughly *no* "
            "vertical break."
        ),
        md("## 3. Trajectories at three key fractions"),
        code(
            "key_indices = [0, 10, len(fractions) - 1]\n"
            "subset = [trajs[i] for i in key_indices]\n"
            "labels = [f'active={fractions[i]:.2f}' for i in key_indices]\n"
            "fig3d = compare_pitches_3d(subset, labels=labels)\n"
            "fig3d.show()"
        ),
        md(
            "## Takeaway\n\n"
            "Pitch movement depends on spin **rate** AND spin **direction**. Two "
            "pitches with identical rpm can produce drastically different break, "
            "depending on how much of that spin is genuinely perpendicular to the "
            "ball's velocity. This is why Statcast publishes 'Active Spin %' as a "
            "first-class metric alongside spin rate."
        ),
    ]
)

# ---------------------------------------------------------------------------
# Notebook 09: Build your own pitch
# ---------------------------------------------------------------------------

nb09 = new_notebook(
    cells=[
        md(
            "# 09 — Build your own pitch\n\n"
            "A guided tour through `PitchRelease.from_mph_rpm_axis(...)`. We'll "
            "build a custom pitch from scratch, simulate it, inspect the "
            "trajectory data structure, and compare it to the closest preset.\n\n"
            "This notebook is the place to play. Edit the parameters, re-run, and "
            "watch the trajectory respond."
        ),
        code(
            "import numpy as np\n"
            "import matplotlib.pyplot as plt\n\n"
            "from pitchphys import simulate, presets\n"
            "from pitchphys.core.pitch import PitchRelease\n"
            "from pitchphys.viz.plot2d import side_view, catcher_view, top_view\n"
            "from pitchphys.viz.plot3d import trajectory_3d, add_spin_axis_arrow"
        ),
        md(
            "## 1. The clock-tilt convention\n\n"
            "Spin axis is described as a clock face viewed from behind home plate. "
            "12:00 means pure backspin (Magnus break straight up); 6:00 means pure "
            "topspin (Magnus break straight down); 3:00 / 9:00 are sidespin.\n\n"
            "Here's a quick clock-face diagram (each tick mark labels the tilt and "
            "the resulting Magnus break direction):"
        ),
        code(
            "fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(aspect='equal'))\n"
            "theta = np.linspace(0, 2*np.pi, 200)\n"
            "ax.plot(np.cos(theta), np.sin(theta), 'k-')\n"
            "for hour in range(1, 13):\n"
            "    angle = np.pi/2 - hour * np.pi/6  # 12 at top, going clockwise\n"
            "    x_label, y_label = 1.15*np.cos(angle), 1.15*np.sin(angle)\n"
            "    ax.text(x_label, y_label, f'{hour:d}', ha='center', va='center', fontsize=11, fontweight='bold')\n"
            "ax.text(0, 1.4, 'lift (Magnus +z)', ha='center', color='tab:blue', fontsize=10)\n"
            "ax.text(0, -1.4, 'drop (Magnus -z)', ha='center', color='tab:red', fontsize=10)\n"
            "ax.text(1.4, 0, 'glove side\\n(Magnus +x)', va='center', color='tab:green', fontsize=10)\n"
            "ax.text(-1.4, 0, 'arm side\\n(Magnus -x)', va='center', color='tab:purple', fontsize=10)\n"
            "ax.set_xlim(-2, 2)\n"
            "ax.set_ylim(-2, 2)\n"
            "ax.set_title('Clock tilt → Magnus break direction (RHP, catcher view)')\n"
            "ax.axis('off')\n"
            "plt.show()"
        ),
        md(
            "## 2. Build a pitch\n\n"
            "Edit any of these parameters and re-run the cell. Try a 1:00 cutter, "
            "a 4:30 sweeper, or a 7:30 sinker."
        ),
        code(
            "my_pitch = PitchRelease.from_mph_rpm_axis(\n"
            "    speed_mph=88.0,         # release speed\n"
            "    spin_rpm=2200.0,        # total spin rate\n"
            "    tilt_clock=2.0,         # 2:00 — slight cut for an RHP\n"
            "    active_spin_fraction=0.85,\n"
            "    release_height_ft=6.0,\n"
            "    release_side_ft=-1.5,   # RHP side\n"
            "    throwing_hand='R',\n"
            ")\n"
            "my_pitch"
        ),
        md("## 3. Simulate"),
        code(
            "traj = simulate(my_pitch)\n"
            "for k, v in traj.break_metrics().items():\n"
            "    print(f'{k:<28} {v:>+8.3f}')"
        ),
        md(
            "## 4. Visualize\n\n"
            "Three matplotlib views + an interactive 3D scene with the spin-axis "
            "arrow at release."
        ),
        code(
            "fig, axes = plt.subplots(1, 3, figsize=(14, 4))\n"
            "side_view(traj, ax=axes[0])\n"
            "axes[0].set_title('Side')\n"
            "catcher_view(traj, ax=axes[1])\n"
            "axes[1].set_title('Catcher')\n"
            "top_view(traj, ax=axes[2])\n"
            "axes[2].set_title('Top')\n"
            "fig.tight_layout()\n"
            "plt.show()"
        ),
        code(
            "fig3d = trajectory_3d(traj, label='my pitch')\n"
            "add_spin_axis_arrow(fig3d, my_pitch, length_ft=2.5)\n"
            "fig3d.show()"
        ),
        md("## 5. Inspect the raw data\n\nEverything's a numpy array."),
        code(
            "print(f'Time samples: {len(traj.time)}')\n"
            "print(f'Position shape: {traj.position.shape}')\n"
            "print(f'Forces tracked: {list(traj.forces)}')\n"
            "print(f'Magnus force at midflight: {traj.forces[\"magnus\"][len(traj.time)//2]}')"
        ),
        md(
            "## 6. Compare to the nearest preset\n\n"
            "If your pitch is fastball-shaped, here's how it stacks up against the "
            "default 4-seam preset."
        ),
        code(
            "preset_traj = simulate(presets.four_seam())\n"
            "print(f'My pitch IVB:        {traj.induced_vertical_break_in:+.2f} in')\n"
            "print(f'Default 4-seam IVB:  {preset_traj.induced_vertical_break_in:+.2f} in')\n"
            "print(f'My pitch horiz:      {traj.horizontal_break_in:+.2f} in')\n"
            "print(f'Default 4-seam horiz: {preset_traj.horizontal_break_in:+.2f} in')"
        ),
        md(
            "## Takeaway\n\n"
            "The full chain: (mph, rpm, tilt, active fraction) → SI conversion → "
            "spin-axis vector → ODE integration → break metrics. Each parameter has "
            "a well-defined physical meaning, and the model exposes every "
            "intermediate quantity (forces, Reynolds number, spin factor, drag/lift "
            "coefficients) on `traj` for inspection."
        ),
    ]
)


def write(notebook, name: str):
    """Inject Colab badge + install cell, then save the notebook."""
    # Cell 0 is the title/intro markdown; rewrite it to include the Colab
    # badge under the H1.
    first_cell = notebook.cells[0]
    if first_cell.cell_type == "markdown":
        first_cell.source = with_colab_badge(first_cell.source, name)
    # Insert the auto-install code cell at index 1 (right after the intro).
    notebook.cells.insert(1, new_code_cell(COLAB_INSTALL_CODE))

    path = OUT_DIR / name
    nbf.write(notebook, path)
    print(f"wrote {path}")


write(nb03, "03_magnus_effect_fastball_curveball.ipynb")
write(nb05, "05_active_spin_vs_gyro_spin.ipynb")
write(nb09, "09_build_your_own_pitch.ipynb")
