# pitchphys

[![PyPI version](https://img.shields.io/pypi/v/pitchphys.svg)](https://pypi.org/project/pitchphys/)
[![Python versions](https://img.shields.io/pypi/pyversions/pitchphys.svg)](https://pypi.org/project/pitchphys/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://github.com/jman4162/pitchphys/actions/workflows/test.yml/badge.svg)](https://github.com/jman4162/pitchphys/actions/workflows/test.yml)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![Open in Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://pitchphys.streamlit.app)

![pitchphys demo](docs/demo.gif)

**An educational Python simulator for baseball pitch aerodynamics, spin, drag, Magnus force, and pitch movement.**

`pitchphys` is a point-mass trajectory simulator that lets you experiment with the dominant first-order physics of a pitched baseball: gravity, drag, and the Magnus effect. Force terms are toggleable so you can see exactly how each one shapes the trajectory. v0.2 adds an interactive 3D Plotly viz layer, a 5-page Streamlit app, and three tutorial notebooks.

## Install matrix

| Goal | Install command |
| --- | --- |
| Core engine only (numpy + scipy) | `pip install pitchphys` |
| Engine + 2D matplotlib plots | `pip install pitchphys[viz]` |
| Engine + 2D + 3D Plotly + Streamlit app | `pip install pitchphys[app]` |
| Local development (everything + tests) | `pip install -e ".[dev,viz,app]"` |

## Quickstart

```python
from pitchphys import simulate
from pitchphys.presets import four_seam

traj = simulate(four_seam(speed_mph=95, spin_rpm=2400))
print(traj.break_metrics())
```

## Interactive app

After `pip install pitchphys[app]`:

```bash
pitchphys-app                 # opens http://localhost:8501
# or, from a source checkout:
streamlit run app/streamlit_app.py
```

The app has five pages:

1. **Pitch Playground** — every slider, animated 3D, full break-metrics row.
2. **Magnus Explorer** — `v`, `ω`, and `ω × v̂` vectors at release.
3. **Fastball vs Curveball** — two pitches side by side.
4. **Active Spin / Gyro** — sweep active fraction at fixed spin rate.
5. **Drag + Environment** — gravity / drag / Magnus toggles, weather, wind.

## Deploy your own copy to Streamlit Cloud

The repo is preconfigured for one-click deployment:

1. Fork or clone this repo to your GitHub account.
2. Sign in at https://share.streamlit.io with your GitHub account.
3. Click **Create app** → pick this repo, branch `main`, and main file path `app/streamlit_app.py`.
4. Click **Deploy**. Build takes ~3 minutes the first time (plotly + scipy wheels).

Streamlit Cloud reads `requirements.txt` (single line `.[app]` — installs the package with the `[app]` extra) and `runtime.txt` (Python 3.12). All app pages, 3D Plotly viz, and physics models run without further configuration.

## Notebooks

Three tutorial notebooks under `notebooks/` walk through the core physics. Click the badge to open in Google Colab — each notebook auto-installs `pitchphys` in the Colab session, no setup needed.

| Notebook | Topic | Open in Colab |
|---|---|---|
| `03_magnus_effect_fastball_curveball.ipynb` | Why a fastball "rises" (SPEC §4.1) | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jman4162/pitchphys/blob/main/notebooks/03_magnus_effect_fastball_curveball.ipynb) |
| `05_active_spin_vs_gyro_spin.ipynb` | Spin rate is not movement (SPEC §4.4) | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jman4162/pitchphys/blob/main/notebooks/05_active_spin_vs_gyro_spin.ipynb) |
| `09_build_your_own_pitch.ipynb` | Guided tour of `from_mph_rpm_axis(...)` | [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jman4162/pitchphys/blob/main/notebooks/09_build_your_own_pitch.ipynb) |

Note: Colab currently runs Python 3.11; if a future Colab downgrade breaks the install, run the notebooks locally via `jupyter lab notebooks/`.

Approximate output for a high-spin 95 mph four-seamer at sea level (default `LyuAeroModel` + 1.5 s spin-decay τ):

| metric | value |
| --- | --- |
| `release_speed_mph` | 95.0 |
| `plate_speed_mph` | ~86.5 |
| `flight_time_s` | ~0.41 |
| `induced_vertical_break_in` | ~+20.5 (positive = "rises" vs spinless) |
| `total_drop_in` | ~24.7 |
| `horizontal_break_in` | ~0 (pure 12:00 backspin) |
| `magnus_break_z_in` | ~+19 |

To run the test suite, lint, and type checks:

```bash
pytest -q
ruff check . && ruff format --check .
mypy src
```

If `import pitchphys` fails after `pip install -e .` because the install lives under `~/Documents` (which inherits a macOS "hidden" flag that Python's `site` module skips), run:

```bash
find .venv -name "*.pth" -exec chflags nohidden {} \;
```

The package's tests don't need this — `pytest`'s `pythonpath = ["src"]` config in `pyproject.toml` works around it.

## What's modeled (v0.2)

**Engine (v0.1.5)**

- Gravity, drag, and Magnus lift on a point mass
- Active spin vs gyro spin (the part of the spin that actually moves the ball)
- **Drag crisis** at low spin via the Lyu 2022 wind-tunnel fit (`LyuAeroModel`, default for `model="magnus"`)
- **Spin decay** `omega(t) = omega_0 * exp(-t/τ)` with default τ = 1.5 s; `spin_decay_tau_s=None` to disable
- **Weather-driven air properties** via `Environment.from_weather(temp_c, pressure_pa, humidity)` (ideal gas + Tetens humidity + Sutherland viscosity)
- Pluggable aerodynamic models (`LyuAeroModel`, `NathanLiftModel`, `SimpleMagnusModel`, `ConstantAeroModel`, `UserDefinedAeroModel`)
- Pedagogical pitch presets (four-seam, curveball, slider, sinker, changeup)
- Break metrics in baseball-friendly units (inches, mph, feet) over an SI core

**Interactive layer (v0.2)**

- 2D Matplotlib helpers (side / catcher / top / compare-pitches)
- 3D Plotly helpers (`trajectory_3d`, `compare_pitches_3d`, `add_spin_axis_arrow`, `add_force_vectors`)
- Animated ball flight (`animate_pitch`, `animate_pitches`) with play/pause/scrub
- 5-page Streamlit app launchable via `pitchphys-app`
- 3 tutorial notebooks under `notebooks/`

## Physics provenance

The default aerodynamic model is calibrated against published baseball wind-tunnel and motion-capture data:

- **`LyuAeroModel`** (default): drag crisis `Cd(Re, S)` and seam-averaged lift `Cl(S)` from Lyu, Smith, Elliott & Kensrud (2022), "The dependence of baseball lift and drag on spin," *Proc IMechE Part P*. PDF in `references/LyuDragLiftSpin.pdf`.
- **`NathanLiftModel`**: bilinear `Cl(S) = 1.5·S` for `S<0.1` and `0.09 + 0.6·S` for `S≥0.1` from Sawicki, Hubbard & Stronge (2003), "How to hit home runs," *Am. J. Phys.* 71:1152–1162. Validated by Nathan (2008), *Am. J. Phys.* 76:119–124 (PDF: `references/ajpfeb08.pdf`). The four-pitch deflection regression in Nathan's Table I is checked in `tests/test_aero_nathan.py`.
- **`SimpleMagnusModel`**: pedagogical `Cl = min(a·S, cl_max)` (Watts & Ferrer 1987 baseline). Kept as a transparent comparison.

## What's deferred

- Statcast import and seam-shifted-wake toy model (v0.3)
- Numba / JAX backends, parameter fitting (v0.4+)

See `SPEC_DRAFT.md` for the full design rationale and roadmap.

## Important caveat

`pitchphys` is an educational point-mass trajectory simulator. It uses empirical aerodynamic models and simplified force terms. Real baseball flight depends on ball variation, seam geometry, atmospheric conditions, release conditions, spin axis, active spin, and non-Magnus effects such as seam-shifted wake. Use it to learn, explore, and prototype — not as a definitive pitch-design engine.

## Coordinate conventions (catcher view)

```
        12 (backspin)
         |
   9 ----+---- 3   (clock-tilt notation; degrees clockwise from 12)
         |
         6 (topspin)
```

For a right-handed pitcher:
- 12:00 → spin axis along **+x** (catcher's right) → upward Magnus on a +y-traveling pitch
- 6:00 → axis along **-x** (topspin)
- 3:00 → axis along **-z** (sidespin)
- 9:00 → axis along **+z** (sidespin)

`throwing_hand="L"` mirrors clock tilt across the 12-6 axis. World-frame axes: `x` = catcher's right, `y` = toward home plate, `z` = up.

## License

MIT.
