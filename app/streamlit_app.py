"""pitchphys educational Streamlit app — landing page."""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="pitchphys — baseball pitch physics",
    page_icon="⚾",
    layout="wide",
)

st.title("pitchphys ⚾ — interactive pitch physics")

st.markdown(
    """
    An educational simulator for baseball pitch trajectories, built around the
    **Magnus effect**, drag, spin axis, active vs gyro spin, and air-density
    sensitivity. Pick a page from the left sidebar to start exploring.

    ## What's on each page

    - **Pitch Playground** — the master sandbox. Every slider, every model,
      animated 3D view of the ball's flight, full break-metric row.
    - **Magnus Explorer** — the geometry of `ω × v_hat`. See exactly which
      direction the Magnus force pushes for a given spin axis.
    - **Fastball vs Curveball** — two pitches side by side, in 3D and from
      the catcher's view. Tweak each independently.
    - **Active Spin / Gyro** — hold spin rate constant, sweep the active-spin
      fraction. Watch movement collapse as gyro spin takes over.
    - **Drag + Environment** — toggle gravity / drag / Magnus, swap atmospheres
      (sea level / Coors / custom weather), turn on wind.

    ## Physics provenance

    The default `model="magnus"` is `LyuAeroModel`, fit to wind-tunnel data
    from Lyu et al. 2022 (drag crisis at Re ≈ 150 k, seam-averaged C_L(S)).
    The `NathanLiftModel` option uses the Sawicki–Hubbard–Stronge bilinear
    `C_L(S)` validated by Nathan 2008. Spin decay defaults to
    `omega(t) = omega_0 · exp(-t/τ)` with τ = 1.5 s.

    All physics references live in `references/` in the source repo (excluded
    from the published GitHub repo for copyright reasons).
    """
)

st.info(
    "Default `LyuAeroModel` produces ~+20 in IVB on a 95 mph 2400 rpm 12:00 "
    "fastball at sea level — within the published Statcast range for elite "
    "high-spin fastballs."
)
