# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Status

This repo is **pre-implementation**. The only file is `SPEC_DRAFT.md`, a detailed spec for an educational Python package (`pitchphys`) that simulates baseball pitch trajectories. There is no `pyproject.toml`, no `src/`, no tests, and no build/lint/test commands yet. When asked to implement features, follow the spec rather than inventing a different architecture, and create the project scaffolding described in SPEC_DRAFT.md §16 unless the user says otherwise.

## Core Architectural Contract (from SPEC_DRAFT.md)

These choices are load-bearing — don't change them without checking with the user.

**Three-layer split.** Core physics engine (no Streamlit, no Plotly), then an optional viz layer, then an optional Streamlit demo app. Streamlit, Plotly, and pybaseball must stay out of the core dependency set; they belong in extras (`[viz]`, `[app]`, `[data]`).

**SI units internally; conversions at the boundary.** Meters, seconds, kg, radians inside the engine. `pitchphys.units` provides mph/rpm/ft/inches helpers for user-facing APIs and metrics. Never let mph or rpm leak into force calculations.

**Right-handed coordinates.** `x` = horizontal, positive to catcher's right; `y` = forward toward home plate; `z` = vertical, positive up. Plate crossing is `y = plate_distance` (default 55 ft, configurable for extension). The spec calls out that spin axis vs. tilt vs. pitcher-view vs. catcher-view is a common source of bugs — always document which convention an output uses, and always expose the spin-axis vector and Magnus-force vector in visualizations.

**Composable, toggleable forces.** Gravity, drag, Magnus, optional non-Magnus/seam-shifted-wake, optional wind. The simulation API must accept a `forces=[...]` list so users can run gravity-only, gravity+drag, full physics, etc. — this is the core educational feature, not a debug knob.

**Active spin is first-class.** Decompose `omega` into `omega_perp` (perpendicular to velocity, drives Magnus) and the gyro component along velocity. Users must be able to specify either a full 3D spin vector or `(spin_rate, spin_axis, active_spin_fraction)`. Do not equate spin rate with movement.

**Aero models are pluggable via a Protocol.** `AeroModel` exposes `cd(Re, S, context)`, `cl(Re, S, context)`, and an optional `non_magnus_force(...)`. Built-ins include `ConstantAeroModel`, `NathanLiftModel`, `SimpleMagnusModel`, `ToySeamShiftedWakeModel`, `UserDefinedAeroModel`. The seam-shifted-wake model is intentionally a humble empirical toy in v1 — do not promise CFD-grade seam resolution.

**Backend strategy: NumPy + SciPy first.** Default integrator is `scipy.integrate.solve_ivp` with event handling for plate crossing. Numba and JAX are optional extras for batch sweeps and differentiable fitting respectively, behind a `backend=` parameter on `simulate_batch`. Do not introduce JAX, Numba, or GPU code into the core path.

## Non-Goals (don't drift into these)

The spec explicitly excludes: full CFD, exact seam-resolved Navier-Stokes, exact prediction of individual MLB pitches, biomechanics/coaching advice, and any claim that spin rate alone or Magnus alone fully determines movement. If a feature request pushes toward these, flag it.

## MVP Scope (v0.1)

Gravity, drag, Magnus, constant + empirical Cd/Cl, pitch release dataclasses, SI units, unit conversions, 2D Matplotlib plots, presets for four-seam/curveball/slider/sinker/changeup, break metrics, and tests for both analytic cases (gravity-only matches projectile motion, no-force is constant velocity) and qualitative behavior (backspin → upward Magnus, pure gyro → near-zero Magnus, gyro slider has high spin but low break). 3D Plotly, the Streamlit app, and Statcast import are deferred to v0.2/v0.3.

## Working with the Spec

`SPEC_DRAFT.md` is the source of truth for design intent. When implementing, prefer to update the spec alongside code if a decision changes, and cite the relevant section number in commits or PRs. Section map: §4 physics background, §7 coordinates, §8 equations of motion, §9 dataclasses, §10 simulation API, §11 output metrics, §16 repo layout, §17 dependencies, §18 versioned scope.
