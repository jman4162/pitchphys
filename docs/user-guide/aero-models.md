# Aerodynamic models

`pitchphys` ships four built-in aerodynamic models plus a `UserDefinedAeroModel` escape hatch. Each implements the `AeroModel` Protocol — `cd(Re, S, ctx)` and `cl(Re, S, ctx)` — and is callable from `simulate(pitch, model="<name>")`.

## At a glance

| Model | `Cd` | `Cl` | Source | Default? |
| --- | --- | --- | --- | --- |
| `LyuAeroModel` | `Cd(Re, S)` empirical fit | `Cl(S)` seam-averaged | Lyu 2022 wind-tunnel | ✅ default |
| `NathanLiftModel` | constant 0.35 | SHS bilinear in S | Sawicki–Hubbard–Stronge 2003 + Nathan 2008 | option |
| `SimpleMagnusModel` | constant 0.35 | `min(a·S, cl_max)` linear | Watts & Ferrer 1987 baseline | option |
| `ConstantAeroModel` | configurable | configurable | none (analytic) | option |
| `UserDefinedAeroModel` | user-supplied | user-supplied | your code | escape hatch |

```python
# Switch model via a string alias:
simulate(pitch, model="magnus")    # default → LyuAeroModel
simulate(pitch, model="nathan")    # NathanLiftModel
simulate(pitch, model="simple")    # SimpleMagnusModel
simulate(pitch, model="constant")  # ConstantAeroModel

# Or pass an instance for custom values:
from pitchphys.aero import ConstantAeroModel
simulate(pitch, model=ConstantAeroModel(cd_value=0.40, cl_value=0.15))
```

## `LyuAeroModel` (default)

**Source**: [Lyu, B., Smith, L., Elliott, J., & Kensrud, J. (2022). "The dependence of baseball lift and drag on spin." *Proc IMechE Part P: J Sports Engineering and Technology* 236(4): 308–314.](https://baseball.physics.illinois.edu/LyuDragLiftSpin.pdf) (DOI 10.1177/17543371221113914)

This is the highest-fidelity option and the default for `model="magnus"`. It captures two real effects that the simpler models miss:

1. **Drag crisis** — at low spin, `C_D` drops from ~0.45 to ~0.32 across `Re ≈ 75k → 175k` (Fig. 5 of the paper).
2. **Spin-dependent drag** — beyond `S ≈ 0.15` the drag crisis is absent and `C_D` rises roughly linearly with `S` (Fig. 3).

Lift is the seam-averaged `C_L(S)` from Fig. 3 / Table 1. Two-seam vs four-seam splits at `S < 0.15` are folded in via the average — a true seam-orientation split is reserved for the v0.3 seam-shifted-wake model.

Implementation uses `np.interp` on small hand-extracted lookup tables; see `src/pitchphys/aero/lyu.py` for the values with figure citations inline.

## `NathanLiftModel`

**Source**: [Sawicki, G. S., Hubbard, M., & Stronge, W. J. (2003). "How to hit home runs: Optimum baseball bat swing parameters for maximum range trajectories." *Am. J. Phys.* 71:1152–1162.](https://ui.adsabs.harvard.edu/abs/2003AmJPh..71.1152S/abstract) Validated by [Nathan, A. M. (2008). "The effect of spin on the flight of a baseball." *Am. J. Phys.* 76:119–124.](https://baseball.physics.illinois.edu/AJP-Feb08.pdf)

Implements the Sawicki–Hubbard–Stronge bilinear `C_L(S)`:

$$C_L = \begin{cases} 1.5 \cdot S & S < 0.1 \\ 0.09 + 0.6 \cdot S & S \ge 0.1 \end{cases}$$

The two pieces agree at `S = 0.1` (both give 0.15), so the function is continuous. Nathan 2008's motion-capture experiment independently measured `C_L` over `v = 50–110 mph` and `S = 0.1–0.6`, concluding *"The parametrization of Ref. 5 is found to give an excellent description of the data in this regime."*

Drag is held at a constant 0.35. Nathan 2008 Fig. 4 shows the actual `C_D` has a weak speed dependence and considerable scatter — `LyuAeroModel` is the better choice for `C_D`.

The four-pitch deflection regression in Nathan's Table I (p. 124) is checked in `tests/test_aero_nathan.py`:

| `v` (mph) | `ω` (rpm) | `S` | Table I (in) | Simulated (`model="nathan"`) |
| --- | --- | --- | --- | --- |
| 75 | 1000 | 0.11 | 16 | ±3 in |
| 75 | 1800 | 0.20 | 21 | ±3 in |
| 90 | 1000 | 0.09 | 14 | ±3 in |
| 90 | 1800 | 0.17 | 19 | ±3 in |

!!! note "History — the misattribution that's been fixed"
    Earlier versions of `pitchphys` (v0.1) used `Cl = 1.5·S / (0.4 + 2.32·S)` and credited it to Nathan 2008. Reading the actual paper (in `references/ajpfeb08.pdf` of the source repo) shows Nathan does **not** propose that formula — the rational fit was a secondary-source misattribution. v0.1.5 swapped in the actual SHS bilinear; the test suite anchors against Nathan's Table I to prevent regression.

## `SimpleMagnusModel`

A pedagogically-clear linear-in-spin-factor model:

$$C_L = \min(a \cdot S, C_{L,\max}), \qquad C_D = 0.35$$

Default `a = 1.0, cl_max = 0.4`. Useful for teaching — it lets you watch "more spin → more break" in a transparent equation. The Watts & Ferrer 1987 wind-tunnel data was consistent with `C_L = S` over the range they measured (low speeds, S = 0.4–1.0).

Not appropriate for fitting against Statcast or for high-fidelity work — both `LyuAeroModel` and `NathanLiftModel` are better-grounded.

## `ConstantAeroModel`

Fixed `C_D = 0.35`, `C_L = 0.20` (configurable via the constructor). Useful only for analytic regression tests where you need a known coefficient. Don't use it for real simulations.

## `UserDefinedAeroModel`

Pass in your own `Callable[[Re, S, ctx], float]` for either coefficient:

```python
from pitchphys.aero import UserDefinedAeroModel

def my_cd(Re, S, ctx):
    # Polynomial fit to your own wind-tunnel data, say.
    return 0.35 + 0.1 * S - 0.5 * (Re / 1e5 - 1.5) ** 2

def my_cl(Re, S, ctx):
    return 1.6 * S / (0.5 + S)   # any callable, including lookup tables

simulate(pitch, model=UserDefinedAeroModel(cd_fn=my_cd, cl_fn=my_cl))
```

The Protocol also exposes `non_magnus_force(t, state, pitch, env) -> np.ndarray` for things like the v0.3 toy seam-shifted-wake — but for now the built-in models all return zero for that hook.

## Picking a model

| Use case | Recommendation |
| --- | --- |
| Learning what Magnus does | `SimpleMagnusModel` (transparent equation) |
| Matching real Statcast numbers | `LyuAeroModel` (default; drag crisis matters) |
| Reproducing Nathan 2008 Table I | `NathanLiftModel` |
| Toy / regression tests | `ConstantAeroModel` |
| Custom fits, lookup tables | `UserDefinedAeroModel` |

For interactive exploration, just stick with the default. The Streamlit app's "Aerodynamic model" selector lets you toggle on the fly and watch how break metrics shift.
