# Tutorials

Three Jupyter notebooks walk through the core physics interactively. Each one is committed to the repo with full executed outputs, and renders inline in this documentation site. To play with them yourself, click the **Colab** badge — Google Colab opens the notebook in a free cloud environment and auto-installs `pitchphys` on first run.

| Tutorial | Topic | Open in Colab |
| --- | --- | --- |
| **03 — Fastball vs curveball** | Why a fastball "rises" while a curveball drops more than gravity alone (SPEC §4.1). Compares trajectories from multiple angles; decomposes forces over time. | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jman4162/pitchphys/blob/main/notebooks/03_magnus_effect_fastball_curveball.ipynb) |
| **05 — Active spin vs gyro spin** | Spin rate alone doesn't determine movement (SPEC §4.4). Holds total spin constant at 2,500 rpm and sweeps `active_spin_fraction` from 0 (pure gyro) to 1 (pure active). | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jman4162/pitchphys/blob/main/notebooks/05_active_spin_vs_gyro_spin.ipynb) |
| **09 — Build your own pitch** | Guided tour through `PitchRelease.from_mph_rpm_axis(...)`. Builds a custom pitch from scratch, inspects the trajectory data structure, and compares to the nearest preset. | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jman4162/pitchphys/blob/main/notebooks/09_build_your_own_pitch.ipynb) |

## Reading order

Read **03 first** if you want to see Magnus in action immediately. Read **05** to internalize why "high-spin" isn't the same as "high-movement". Read **09** when you're ready to build a pitch parameter by parameter — it's the bridge to programming with the package.

## What the notebooks won't show you

The notebooks demonstrate the **API surface** and the **physics behavior**. For deeper coverage of:

- The four forces and what they do → [Physics primer](user-guide/physics-primer.md)
- Spin-axis conventions and how to interpret tilt → [Coordinates](user-guide/coordinates.md)
- Choosing the right aerodynamic model for your use case → [Aerodynamic models](user-guide/aero-models.md)
- Weather and atmospheric effects → [Environment & weather](user-guide/environment.md)
- The full API surface (every public function and class) → [API reference](api.md)

## Want to try a slider before reading code?

The Streamlit app at [pitchphys.streamlit.app](https://pitchphys.streamlit.app) covers the same ground as the notebooks but with interactive sliders. The **Pitch Playground** page in particular is essentially "notebook 09 with sliders".
