# pitchphys

**An educational Python simulator for baseball pitch aerodynamics, spin, drag, Magnus force, and pitch movement.**

`pitchphys` is a point-mass trajectory simulator that lets you experiment with the dominant first-order physics of a pitched baseball: gravity, drag, and the Magnus effect. Force terms are toggleable so you can see exactly how each one shapes the trajectory.

## Quickstart

```bash
pip install -e ".[dev,viz]"
```

```python
from pitchphys import simulate
from pitchphys.presets import four_seam

traj = simulate(four_seam(speed_mph=95, spin_rpm=2400))
print(traj.break_metrics())
```

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

## What's modeled in v0.1.5

- Gravity, drag, and Magnus lift on a point mass
- Active spin vs gyro spin (the part of the spin that actually moves the ball)
- **Drag crisis** at low spin via the Lyu 2022 wind-tunnel fit (`LyuAeroModel`, default for `model="magnus"`)
- **Spin decay** `omega(t) = omega_0 * exp(-t/τ)` with default τ = 1.5 s; `spin_decay_tau_s=None` to disable
- **Weather-driven air properties** via `Environment.from_weather(temp_c, pressure_pa, humidity)` (ideal gas + Tetens humidity + Sutherland viscosity)
- Pluggable aerodynamic models (`LyuAeroModel`, `NathanLiftModel`, `SimpleMagnusModel`, `ConstantAeroModel`, `UserDefinedAeroModel`)
- Pedagogical pitch presets (four-seam, curveball, slider, sinker, changeup)
- Break metrics in baseball-friendly units (inches, mph, feet) over an SI core
- 2D Matplotlib helpers (side view, catcher view, top view, pitch comparison)

## Physics provenance

The default aerodynamic model is calibrated against published baseball wind-tunnel and motion-capture data:

- **`LyuAeroModel`** (default): drag crisis `Cd(Re, S)` and seam-averaged lift `Cl(S)` from Lyu, Smith, Elliott & Kensrud (2022), "The dependence of baseball lift and drag on spin," *Proc IMechE Part P*. PDF in `references/LyuDragLiftSpin.pdf`.
- **`NathanLiftModel`**: bilinear `Cl(S) = 1.5·S` for `S<0.1` and `0.09 + 0.6·S` for `S≥0.1` from Sawicki, Hubbard & Stronge (2003), "How to hit home runs," *Am. J. Phys.* 71:1152–1162. Validated by Nathan (2008), *Am. J. Phys.* 76:119–124 (PDF: `references/ajpfeb08.pdf`). The four-pitch deflection regression in Nathan's Table I is checked in `tests/test_aero_nathan.py`.
- **`SimpleMagnusModel`**: pedagogical `Cl = min(a·S, cl_max)` (Watts & Ferrer 1987 baseline). Kept as a transparent comparison.

## What's deferred

- 3D Plotly visualizations and animation (v0.2)
- Streamlit educational app (v0.2)
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
