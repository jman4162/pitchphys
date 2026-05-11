# Pitch presets

`pitchphys.presets` ships five archetype constructors that return ready-to-simulate `PitchRelease` objects. They're convenience wrappers around `PitchRelease.from_mph_rpm_axis(...)` with reasonable defaults baked in.

```python
from pitchphys import simulate
from pitchphys.presets import four_seam, curveball, slider, sinker, changeup

traj_fb = simulate(four_seam())
traj_cb = simulate(curveball(speed_mph=78))    # override defaults
```

## The five presets

| Preset | Default speed | Default spin | Default tilt | Active spin | Archetype |
| --- | --- | --- | --- | --- | --- |
| `four_seam()` | 95 mph | 2400 rpm | 12:00 | 0.95 | High-spin lift fastball |
| `curveball()` | 80 mph | 2700 rpm | 6:00 | 0.85 | Top-spin drop |
| `slider()` | 85 mph | 2500 rpm | 9:00 | 0.30 | Gyro-dominant — high spin, low break |
| `sinker()` | 92 mph | 2200 rpm | 8:00 | 0.85 | Lower-tilt arm-side run + drop |
| `changeup()` | 84 mph | 1700 rpm | 1:00 | 0.85 | Lower spin, slight tail |

All defaults are RHP (`throwing_hand="R"`). Pass `throwing_hand="L"` to mirror.

## What each preset is — and isn't

These are **pedagogical archetypes**, not MLB averages. The point is to give every demo a sensible starting point that produces a recognizable trajectory: a four-seam preset that lifts visibly, a curveball that drops visibly, a slider that demonstrates the gyro-spin effect.

They are **not** calibrated against any specific pitcher's repertoire or any specific Statcast cluster. Real four-seam fastballs vary widely: a Spencer Strider 2024 fastball is more like 98 mph at 2400 rpm with a tilt closer to 1:00 than 12:00. A typical MLB curveball might be 78 mph at 2600 rpm.

To model a specific pitcher:

```python
strider_fb = four_seam(
    speed_mph=98,
    spin_rpm=2400,
    tilt_clock=1.0,            # ~1:00 not 12:00
    active_spin_fraction=0.95,
)
```

Every constructor accepts the full set of `from_mph_rpm_axis` parameters; the preset just supplies defaults for the ones you don't pass.

## Caveat from SPEC §6.6

From the project specification's "no overclaiming" principle (SPEC §6.6 and §19):

> The package should not claim to exactly reproduce MLB pitches without full release, spin-axis, seam-orientation, environmental, and ball-property data.

A four-seam preset gets you a *recognizable* fastball trajectory. It does not give you Strider's specific 98 mph fastball. For real-pitch matching, use the [Statcast comparison form](https://pitchphys.streamlit.app) on the Pitch Playground app page — it lets you enter observed values from Baseball Savant and see how the simulation deviates.

## Use the gyro slider to teach active-spin

The `slider()` preset deliberately sets `active_spin_fraction=0.30` — much lower than the other presets. This demonstrates the SPEC §4.4 lesson that **spin rate is not movement**: the slider has 2,500 rpm of spin, but only 30% of it is perpendicular to velocity, so the Magnus break is much smaller than a four-seam with similar total spin.

Try this side-by-side in the [Fastball-vs-Curveball app page](https://pitchphys.streamlit.app) — pick `four_seam` on the left, `slider` on the right, and compare their break magnitudes.

## Building your own presets

If you find yourself reusing a custom configuration, just write a tiny factory function:

```python
def my_sweeper(speed_mph=85, spin_rpm=2800, **kw):
    return PitchRelease.from_mph_rpm_axis(
        speed_mph=speed_mph,
        spin_rpm=spin_rpm,
        tilt_clock=10.0,           # 10:00 — heavy gloveside break
        active_spin_fraction=0.80,
        **kw,
    )
```

There's nothing magical about the built-in presets — they're 5–10 lines each in `src/pitchphys/presets/pitches.py`. Treat them as starting points.
