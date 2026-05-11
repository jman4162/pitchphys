# pitchphys

**An educational Python simulator for baseball pitch aerodynamics, spin, drag, Magnus force, and pitch movement.**

`pitchphys` is a point-mass trajectory simulator that lets you experiment with the dominant first-order physics of a pitched baseball: gravity, drag, and the Magnus effect. Force terms are toggleable so you can see exactly how each one shapes the trajectory. The package ships with a 3D Plotly visualization layer, a 5-page interactive Streamlit app, and three tutorial notebooks.

[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://pitchphys.streamlit.app){ .md-button .md-button--primary }
[Browse the API reference](api.md){ .md-button }
[Read the physics primer](user-guide/physics-primer.md){ .md-button }

## Install

| Goal | Install command |
| --- | --- |
| Core engine only (numpy + scipy) | `pip install pitchphys` |
| Engine + 2D matplotlib + 3D plotly viz | `pip install "pitchphys[viz]"` |
| Engine + viz + interactive Streamlit app | `pip install "pitchphys[app]"` |
| Local development (everything + tests + docs) | `pip install -e ".[dev,viz,app,docs]"` |

## 30-second quickstart

```python
from pitchphys import simulate
from pitchphys.presets import four_seam

traj = simulate(four_seam(speed_mph=95, spin_rpm=2400))
print(traj.break_metrics())
```

Approximate output for a 95 mph 2400 rpm 12:00 (pure backspin) fastball at sea level, using the default `LyuAeroModel` with 1.5 s spin-decay τ:

| metric | value |
| --- | --- |
| `release_speed_mph` | 95.0 |
| `plate_speed_mph` | ~86.5 |
| `flight_time_s` | ~0.41 |
| `induced_vertical_break_in` | ~+20.5 (positive = "rises" vs spinless) |
| `total_drop_in` | ~24.7 |
| `horizontal_break_in` | ~0 |
| `magnus_break_z_in` | ~+19 |

## Three ways to use it

### :material-cube-outline: As a Python library

Import `simulate`, build a `PitchRelease`, get back a `TrajectoryResult` with full per-step diagnostics. See the [API reference](api.md).

### :material-rocket-launch-outline: As an interactive web app

Launch the bundled Streamlit app locally with `pitchphys-app`, or use the [hosted version on Streamlit Cloud](https://pitchphys.streamlit.app). Five pages cover the pitch playground, Magnus geometry, two-pitch comparison, active-spin sweep, and the drag/environment interactions.

### :material-notebook-outline: As tutorial notebooks

Three guided Jupyter notebooks walk through the core physics. Each opens in Google Colab with a single click and auto-installs `pitchphys` in the Colab session. See [Tutorials](tutorials.md).

## Physics provenance

The default `model="magnus"` is `LyuAeroModel`, fit to wind-tunnel data from Lyu, Smith, Elliott & Kensrud (2022). The `NathanLiftModel` option uses the Sawicki–Hubbard–Stronge bilinear `C_L(S)` independently validated by Nathan 2008. See [Aerodynamic models](user-guide/aero-models.md) for source citations and tradeoffs.

## Important caveat

`pitchphys` is an educational point-mass trajectory simulator. It uses empirical aerodynamic models and simplified force terms. Real baseball flight depends on ball variation, seam geometry, atmospheric conditions, release conditions, spin axis, active spin, and non-Magnus effects such as seam-shifted wake. Use it to learn, explore, and prototype — not as a definitive pitch-design engine.
