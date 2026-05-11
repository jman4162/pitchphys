# Environment and weather

The `Environment` dataclass holds air density, dynamic viscosity, gravity, and wind. It's what `simulate(pitch, env=env)` reads to compute drag and Magnus forces. Three constructors cover the common cases.

## Sea-level standard

```python
from pitchphys import Environment
env = Environment.sea_level()
# Environment(air_density_kg_m3=1.225, dynamic_viscosity_pa_s=1.81e-5,
#             gravity_m_s2=9.80665, wind_m_s=array([0., 0., 0.]))
```

This is the default if you don't pass `env` to `simulate()`. ISA standard atmosphere at 15 °C, sea-level pressure.

## Coors Field

```python
env = Environment.coors_field()
# air_density_kg_m3 = 1.00 (approximate)
```

Denver's ~5,200 ft elevation gives ~18% less air density than sea level. A fastball at Coors loses less speed to drag (plate speed ~88 mph vs ~86 mph at sea level for a 95 mph release) AND has less Magnus force (since both drag and Magnus scale linearly with density). The net effect on IVB is a wash for fastballs but matters a lot for breaking pitches.

This is a hardcoded approximation. For exact local conditions, use `from_weather` below.

## From weather

```python
env = Environment.from_weather(
    temp_c=25.0,           # game-time temperature
    pressure_pa=98_000.0,  # actual atmospheric pressure
    humidity=0.6,          # relative humidity (0..1)
)
```

Builds an `Environment` from real weather data. Uses:

1. **Ideal-gas law** for dry-air density: $\rho_d = P_d / (R_d T)$
2. **Tetens equation** for water-vapor saturation pressure: $P_\text{sat}(T) = 610.78 \, e^{17.27 T_c / (T_c + 237.3)}$ Pa
3. **Sutherland's law** for dynamic viscosity vs temperature: $\mu(T) = \mu_\text{ref} (T / T_\text{ref})^{1.5} (T_\text{ref} + S) / (T + S)$

The humid-air density is a mixture of dry-air and water-vapor partial pressures.

### Counter-intuitive fact: humid air is LESS dense than dry air

Most people guess that humid air is "thicker" — it isn't. Water vapor has molar mass ~18 g/mol, while the nitrogen/oxygen mix that makes up most of dry air averages ~29 g/mol. So replacing dry-air molecules with water-vapor molecules at the same pressure and temperature **lowers** the average molar mass and therefore the density. At 30 °C and sea-level pressure, going from 0% to 100% relative humidity drops the density by ~1%.

```python
dry  = Environment.from_weather(temp_c=30.0, pressure_pa=101_325.0, humidity=0.0)
wet  = Environment.from_weather(temp_c=30.0, pressure_pa=101_325.0, humidity=1.0)
print(f"Dry:   {dry.air_density_kg_m3:.4f} kg/m³")
print(f"Humid: {wet.air_density_kg_m3:.4f} kg/m³")
# Dry:   1.1644 kg/m³
# Humid: 1.1517 kg/m³  (~1% less)
```

A 1% drop in air density means ~1% less drag and ~1% less Magnus break — small, but not zero. Hot, humid weather (a typical August game) gives slightly less break than cold, dry weather.

### Temperature sensitivity (constant pressure)

Higher temperature → lower density (ideal gas). Sutherland's law also bumps viscosity slightly, but the density effect dominates for trajectory work.

| Temp | Density (kg/m³) | Δ vs 15 °C |
| --- | --- | --- |
| 0 °C | 1.290 | +5.3% |
| 15 °C | 1.225 | (ref) |
| 25 °C | 1.184 | −3.4% |
| 35 °C | 1.146 | −6.4% |

### Pressure sensitivity (constant temperature)

Density is linear in pressure. Coors Field (~83 kPa) is at 82% of sea-level pressure, so density ~82% of sea-level value (~1.00 kg/m³). High-pressure systems give slightly more drag than low-pressure systems.

## Wind

```python
import numpy as np
env = Environment(
    air_density_kg_m3=1.225,
    dynamic_viscosity_pa_s=1.81e-5,
    gravity_m_s2=9.80665,
    wind_m_s=np.array([0.0, -5.0, 0.0]),   # 5 m/s headwind
)
```

Wind enters drag through the **relative velocity**: $\mathbf{v}_\text{rel} = \mathbf{v}_\text{ball} - \mathbf{v}_\text{wind}$. A 5 m/s (~11 mph) headwind makes the ball "feel" 5 m/s faster, scaling drag by `((v + 5) / v)^2`.

Vertical wind components (the `vz` axis) are physically unusual but technically supported. A crosswind component (`vx`) creates an asymmetry that the Magnus force on a vertical-spin pitch wouldn't otherwise have.

## Putting it all together

The Drag + Environment page of the Streamlit app lets you toggle gravity / drag / Magnus on or off independently while varying temperature, pressure, humidity, and wind — a useful way to build intuition for how each environmental knob shifts the trajectory.
