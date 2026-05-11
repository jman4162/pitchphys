# Changelog

This page summarizes user-facing changes per release. GitHub Releases (linked at the top of each section) contain the full commit log.

## v0.2.0 — Interactive layer + Tier-1 adoption polish

**Published**: May 2026 · [PyPI](https://pypi.org/project/pitchphys/0.2.0/) · [GitHub tag](https://github.com/jman4162/pitchphys/releases/tag/v0.2.0)

Major release. Turned the engine into something you can play with in a browser.

### Added

- **5-page Streamlit app** (`pitchphys-app` console script): Pitch Playground, Magnus Explorer, Fastball-vs-Curveball, Active-Spin/Gyro, Drag+Environment.
- **3D Plotly visualization**: `trajectory_3d`, `compare_pitches_3d`, `add_spin_axis_arrow`, `add_force_vectors`.
- **Animated ball flight**: `animate_pitch` and `animate_pitches` with play/pause/scrub via Plotly frames.
- **3 tutorial notebooks** under `notebooks/`, Colab-runnable: `03_magnus_effect_fastball_curveball.ipynb`, `05_active_spin_vs_gyro_spin.ipynb`, `09_build_your_own_pitch.ipynb`. Each auto-installs `pitchphys` on Colab.
- **Streamlit Cloud configs** (`.streamlit/config.toml`, `requirements.txt`, `runtime.txt`) for one-click deployment.
- **Strike-zone "is it a strike?" indicator** on every relevant page.
- **URL state encoding** — every Pitch Playground slider is captured in the URL, so you can share a link to any pitch you build.
- **Cross-page pitch persistence** via `st.session_state["canonical_pitch"]`.
- **Download buttons** for trajectory CSV, break-metrics JSON, and 3D-figure HTML.
- **Statcast comparison form** on the Pitch Playground: observed/simulated/Δ columns for release speed, spin rate, tilt, IVB, horizontal break.
- **GitHub Actions** for CI tests, docs deploy, PyPI publish (OIDC trusted publishing), and Streamlit Cloud keepalive cron.
- **PyPI publishing**: `pip install pitchphys` now works.

### Changed

- `pyproject.toml` now declares `[viz]`, `[app]`, `[dev]`, `[docs]` optional-dependency groups.
- Console script `pitchphys-app` resolves the bundled `app/streamlit_app.py` via `importlib.resources` with a source-checkout fallback.

### Tests

- 174 → 185 tests passing. New: `tests/test_plot3d.py`, `tests/test_animation.py`, `tests/test_app_utils.py`, `tests/test_app_launcher.py`, `tests/test_app_extras.py`.

## v0.1.5 — Physics fidelity upgrades

**Published**: May 2026 (commit `d8846c6` on `main`).

The physics core got calibrated against published wind-tunnel and motion-capture data.

### Added

- **`LyuAeroModel`** — drag-crisis `Cd(Re, S)` and seam-averaged `Cl(S)` from Lyu, Smith, Elliott & Kensrud (2022). Now the default for `model="magnus"`.
- **Spin decay** — `omega(t) = omega_0 · exp(-t/τ)` with default τ = 1.5 s. Pass `spin_decay_tau_s=None` to disable.
- **`Environment.from_weather(temp_c, pressure_pa, humidity)`** — ideal gas + Tetens humidity correction + Sutherland viscosity.
- **Regression test against Nathan 2008 Table I** — 4-pitch deflection sanity check pins the model to published numbers.

### Changed

- **`NathanLiftModel` rewritten** to use the Sawicki–Hubbard–Stronge (2003) bilinear `Cl(S)` that Nathan 2008 actually validated. The previous misattributed rational fit was removed (v0.1 had it credited to Nathan; the actual paper does not propose that formula).

### Tests

- 110 → 147 tests passing. Anchored to Nathan Table I.

## v0.1.0 — Initial release

**Published**: May 2026 (commit `d8846c6` as "Initial commit").

The first usable version. Core engine + 2D matplotlib viz + 5 pedagogical pitch presets.

### Added

- **Core simulator**: gravity, drag, Magnus (simple linear-in-S model), composable force toggles, scipy `solve_ivp` integrator with plate-crossing event termination.
- **Data models**: `Baseball`, `Environment`, `PitchRelease`, `TrajectoryResult`.
- **Pluggable `AeroModel` Protocol** with `SimpleMagnusModel`, `NathanLiftModel` (initial rational form), `ConstantAeroModel`, `UserDefinedAeroModel`.
- **Pitch presets**: `four_seam`, `curveball`, `slider`, `sinker`, `changeup`.
- **2D Matplotlib helpers**: `side_view`, `catcher_view`, `top_view`, `compare_pitches`.
- **Break metrics in baseball-friendly units** (mph, ft, in) over an SI engine.
- **110 tests** with analytic-projectile and qualitative-behavior regressions.
- **Clock-tilt spin-axis convention** pinned in `pitchphys.coordinates`.
- **MIT license**, Python ≥3.11, ruff + mypy clean.
