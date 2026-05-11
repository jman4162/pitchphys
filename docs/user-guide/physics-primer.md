# Physics primer

This page walks through the four forces that govern a pitched baseball's trajectory in `pitchphys`, what each one does, and what changes when you toggle it off. The goal is intuition, not derivation — for full equations and references, see [SPEC §4](https://github.com/jman4162/pitchphys/blob/main/SPEC_DRAFT.md) in the source repo.

## The four forces

A baseball in flight experiences four physical effects in `pitchphys`:

1. **Gravity** — always pulls the ball downward.
2. **Drag** — opposes velocity; slows the ball.
3. **Magnus lift** — perpendicular to both velocity and spin axis; the source of pitch movement.
4. **Spin decay** (optional) — angular velocity shrinks over flight time.

`simulate(pitch, forces=["gravity", "drag", "magnus"])` is the default. Toggling any subset on/off is a first-class educational feature — try `forces=["gravity"]` to see what a spinless pitch would do.

## 1. Gravity

$$\mathbf{F}_g = -m g \hat{\mathbf{z}}$$

The simplest force. With only gravity, the ball follows a parabola: $z(t) = z_0 + v_{z,0} t - \tfrac{1}{2} g t^2$. Default `g = 9.80665 m/s²`.

**What "rising fastball" really means.** A fastball never *literally* rises in MLB conditions — gravity always pulls it down. But the Magnus force on a high-backspin pitch counteracts a portion of gravity's drop, so the ball ends up ~20 inches higher at the plate than a spinless equivalent. That delta — the **induced vertical break (IVB)** — is what makes the pitch look like it "rises" to the hitter.

`pitchphys` reports IVB as `traj.induced_vertical_break_in`. Positive = above the no-force projectile path at the same flight time.

## 2. Drag

$$\mathbf{F}_D = -\tfrac{1}{2} \rho \, C_D \, A \, |\mathbf{v}_{\text{rel}}| \, \mathbf{v}_{\text{rel}}$$

Drag points opposite the ball's velocity (relative to wind) and scales with $|v|^2$. It slows the ball from release to plate, which both reduces the time gravity has to act and the time Magnus has to lift.

**The drag crisis.** $C_D$ is not constant. At low spin, $C_D$ drops sharply across $\text{Re} \approx 75\text{k} \to 175\text{k}$ — a phenomenon called the *drag crisis*. The default `LyuAeroModel` captures this; the simpler `ConstantAeroModel` uses $C_D = 0.35$ throughout.

**Drag and air density.** Drag scales linearly with air density $\rho$. A baseball at Coors Field (1.00 kg/m³, ~5,200 ft elevation) experiences ~18% less drag than at sea level (1.225 kg/m³) — which is why fly balls carry farther in Denver. See [Environment & weather](environment.md).

## 3. Magnus lift

$$\mathbf{F}_M = \tfrac{1}{2} \rho \, C_L \, A \, |\mathbf{v}_{\text{rel}}|^2 \, \widehat{(\boldsymbol{\omega} \times \mathbf{v}_{\text{rel}})}$$

The Magnus force is perpendicular to both velocity and spin axis, pointing in the direction $\boldsymbol{\omega} \times \mathbf{v}_{\text{rel}}$. The magnitude depends on the **spin factor** $S = R \, |\boldsymbol{\omega}_\perp| \,/\, |\mathbf{v}|$.

- **Backspin** (axis perpendicular to velocity, pointing "right" in the catcher view): Magnus points **up**. Fastballs.
- **Topspin**: Magnus points **down**. Curveballs.
- **Sidespin**: Magnus points **left or right**. Sliders, sweepers.
- **Gyrospin** (axis aligned with velocity): Magnus is **zero**.

The lift coefficient $C_L$ is what each aerodynamic model in `pitchphys.aero` specifies:

- `LyuAeroModel` (default): empirical fit from Lyu 2022 wind-tunnel data.
- `NathanLiftModel`: Sawicki–Hubbard–Stronge bilinear: $C_L = 1.5 S$ for $S < 0.1$, $C_L = 0.09 + 0.6 S$ for $S \ge 0.1$.
- `SimpleMagnusModel`: pedagogical $C_L = \min(a S, C_{L,\max})$.

See [Aerodynamic models](aero-models.md) for tradeoffs.

## 4. Active spin vs gyro spin

Not all spin produces movement. Only the component of $\boldsymbol{\omega}$ **perpendicular to velocity** contributes to the Magnus force. The parallel component (gyro spin) doesn't move the ball.

`pitchphys` exposes this as the `active_spin_fraction` parameter on `PitchRelease.from_mph_rpm_axis(...)`:

| `active_spin_fraction` | Meaning |
| --- | --- |
| `1.0` | All spin is perpendicular to velocity — full Magnus break. |
| `0.95` | 95% active — typical of a high-spin 4-seam fastball. |
| `0.30` | 30% active — gyro slider archetype. |
| `0.0` | Pure gyro — no Magnus break (in theory). |

In practice, even a 0% active-spin pitch picks up a small amount of Magnus mid-flight, because gravity bends $\mathbf{v}_{\text{rel}}$ while $\boldsymbol{\omega}$ stays constant in the world frame, so the perpendicular component grows slightly over flight.

**Spin rate is not movement.** A 2,500 rpm gyro slider has the same total spin as a 2,500 rpm 4-seam fastball — and yet the slider has roughly no vertical break. This is why Statcast publishes "Active Spin %" as a first-class metric alongside spin rate. Try the [Active Spin / Gyro Streamlit page](https://pitchphys.streamlit.app) to see it interactively.

## 5. Spin decay (optional)

$$\boldsymbol{\omega}(t) = \boldsymbol{\omega}_0 \, e^{-t / \tau}$$

Real baseballs lose ~10–20% of their spin over the 0.4 s flight to the plate. By default `simulate(...)` uses `spin_decay_tau_s=1.5`, giving ~23% decay over a typical fastball flight. Pass `spin_decay_tau_s=None` to disable (matches SPEC §8.1 strict reading and Nathan 2008's fit assumption — important when comparing to specific published numbers).

## What changes when you toggle a force off

Try this in the [Pitch Playground](https://pitchphys.streamlit.app) or as Python code:

```python
from pitchphys import simulate
from pitchphys.presets import four_seam

pitch = four_seam(speed_mph=95, spin_rpm=2400)

# Each successive simulation adds one more force.
g_only       = simulate(pitch, forces=["gravity"])
g_drag       = simulate(pitch, forces=["gravity", "drag"])
g_drag_magnus = simulate(pitch, forces=["gravity", "drag", "magnus"])  # default

print(f"Gravity only:        IVB {g_only.induced_vertical_break_in:+.1f} in")
print(f"+drag:               IVB {g_drag.induced_vertical_break_in:+.1f} in")
print(f"+Magnus (full):      IVB {g_drag_magnus.induced_vertical_break_in:+.1f} in")
```

Each force adds an additional ~5–20 inch deviation from the previous trajectory. The Magnus contribution alone is what distinguishes a high-IVB fastball from a sinker thrown at the same speed and spin rate.

## Further reading

- The **Lyu 2022** paper is the primary source for the default `Cd(Re, S)` and seam-averaged `Cl(S)` fits. Available open-access at [baseball.physics.illinois.edu](https://baseball.physics.illinois.edu/LyuDragLiftSpin.pdf).
- The **Nathan 2008** paper validates the SHS bilinear `Cl(S)` and provides the reference deflection table used in `tests/test_aero_nathan.py`. *Am. J. Phys.* 76:119–124.
- The **Statcast TPT** trajectory calculator (Kagan & Nathan 2017) is the pedagogical reference for Statcast metric definitions.
