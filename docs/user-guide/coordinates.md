# Coordinates and spin-axis convention

`pitchphys` pins **one** spin-axis convention as the single source of truth, defined in [`pitchphys.coordinates`](../api.md#pitchphys.coordinates). Every other module — the integrator, the force callables, the visualizers — reads from this convention. If you remember nothing else from this page, remember: **clock-tilt direction = Magnus break direction** under our convention.

## World frame (right-handed)

```
   z (up)
   |
   |
   +------ x (catcher's right)
  /
 /
y (forward, toward home plate)
```

- **`x`** = horizontal, positive to the **catcher's right** (when looking from behind home plate toward the pitcher).
- **`y`** = forward, positive **from release toward home plate**. A pitch's initial velocity is mostly +y.
- **`z`** = vertical, positive **up**.

The plate sits at `y = DEFAULT_PLATE_DISTANCE_M ≈ 16.76 m` (55 ft) by default — that's the integrator's termination event.

## Clock tilt (catcher view)

```
        12 (backspin)
         |
   9 ----+---- 3
         |
         6 (topspin)
```

The clock face is viewed from **behind home plate looking toward the pitcher**. For a right-handed pitcher (RHP), the mapping from clock tilt to spin axis is:

| Clock tilt | Spin-axis vector | Magnus break direction |
| --- | --- | --- |
| **12:00** | `+x` | `+z` ("rise" — straight up) |
| **3:00** | `-z` | `+x` (catcher's right) |
| **6:00** | `-x` | `-z` (straight down) |
| **9:00** | `+z` | `-x` (catcher's left) |

The mapping is a planar rotation in the catcher-view `(x, z)` plane:

$$\text{angle} = -\pi \cdot \text{tilt}_\text{clock} / 6 \qquad \text{axis} = (\cos(\text{angle}), 0, \sin(\text{angle}))$$

## Why "tilt = break direction" is intentional

For a pitch traveling along `+y`, the Magnus force is $\mathbf{F}_M \propto \boldsymbol{\omega} \times \hat{\mathbf{v}}$. With $\hat{\mathbf{v}} = +\hat{\mathbf{y}}$:

- Axis $+\hat{\mathbf{x}}$ (12:00): $\hat{\mathbf{x}} \times \hat{\mathbf{y}} = +\hat{\mathbf{z}}$ → break up ✓
- Axis $-\hat{\mathbf{z}}$ (3:00): $-\hat{\mathbf{z}} \times \hat{\mathbf{y}} = +\hat{\mathbf{x}}$ → break right ✓
- Axis $-\hat{\mathbf{x}}$ (6:00): $-\hat{\mathbf{x}} \times \hat{\mathbf{y}} = -\hat{\mathbf{z}}$ → break down ✓
- Axis $+\hat{\mathbf{z}}$ (9:00): $+\hat{\mathbf{z}} \times \hat{\mathbf{y}} = -\hat{\mathbf{x}}$ → break left ✓

It's a happy consequence of the right-hand rule. Under this convention, the **clock-tilt number you specify is the direction the Magnus force pushes** — you don't have to mentally compute a cross product to predict break direction.

## RHP vs LHP

A LHP throwing the same pitch type as a RHP would have a mirrored spin axis. `pitchphys` handles this via the `throwing_hand="L"` argument:

```python
PitchRelease.from_mph_rpm_axis(
    speed_mph=95, spin_rpm=2400, tilt_clock=1.0,
    throwing_hand="L",   # mirrors the tilt across the 12–6 axis
)
```

Under the convention, `throwing_hand="L"` with `tilt_clock=T` produces the same axis as `throwing_hand="R"` with `tilt_clock=12 - T`. So a LHP at 1:00 maps to the same axis as an RHP at 11:00.

## Spin axis vs movement direction

!!! warning "Pitfall — spin axis is NOT movement direction"
    A common confusion: the **spin axis** (the direction `ω` points) is **not** the same as the **movement direction** (the direction the ball breaks). They are perpendicular.

    Example: a 12:00-tilt fastball has its spin axis pointing along `+x` (catcher's right), but the ball breaks **up** (+z). The Magnus force is 90° from the spin axis.

    Statcast and many baseball-physics resources use multiple conventions interchangeably (catcher view vs pitcher view, clock-of-axis vs clock-of-break). `pitchphys` documents its single convention here and uses it consistently across the engine, the app, and the visualizations.

## Active spin and gyro spin

The 3D `pitch.spin_axis` vector returned by `PitchRelease` mixes both **active spin** (perpendicular to velocity, drives Magnus) and **gyro spin** (parallel to velocity, drives nothing). The `active_spin_fraction` parameter on `from_mph_rpm_axis` splits them:

```python
PitchRelease.from_mph_rpm_axis(
    speed_mph=95, spin_rpm=2400, tilt_clock=12,
    active_spin_fraction=0.95,   # 95% of spin is active, 5% gyro
)
```

The internal decomposition lives in `pitchphys.coordinates.decompose_omega(omega, v_hat)`. See [Physics primer §4](physics-primer.md#4-active-spin-vs-gyro-spin) for more.

## Strike-zone constants

For visualization (and the "is it a strike?" indicator in the Streamlit app), `pitchphys.coordinates` exposes:

| Constant | Value | Meaning |
| --- | --- | --- |
| `STRIKE_ZONE_TOP_FT` | `3.5` | Top of the rule-book strike zone |
| `STRIKE_ZONE_BOTTOM_FT` | `1.5` | Bottom of the rule-book strike zone |
| `STRIKE_ZONE_HALF_WIDTH_FT` | `8.5/12` | Half the plate width (17 in plate, half-width 8.5 in) |

These are educational approximations; real MLB strike-zone calls vary by hitter height.
