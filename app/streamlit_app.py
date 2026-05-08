"""pitchphys educational Streamlit app — landing page."""

from __future__ import annotations

from pathlib import Path

import streamlit as st

st.set_page_config(
    page_title="pitchphys — baseball pitch physics",
    page_icon="⚾",
    layout="wide",
)

# Repo-root-relative path to the screenshots directory. Works both when
# run from `streamlit run app/streamlit_app.py` (cwd=repo root) and when
# launched via `pitchphys-app` (file lives under pitchphys/_app/).
_REPO_ROOT_CANDIDATES = (
    Path(__file__).resolve().parents[1],  # source-checkout: app/ -> repo
    Path(__file__)
    .resolve()
    .parents[2],  # installed wheel: pitchphys/_app -> pitchphys -> site-packages (no images here)
    Path.cwd(),  # streamlit run cwd
)
_SCREENSHOTS_DIR: Path | None = None
for _root in _REPO_ROOT_CANDIDATES:
    if (_root / "docs" / "screenshots").is_dir():
        _SCREENSHOTS_DIR = _root / "docs" / "screenshots"
        break

st.title("pitchphys ⚾ — interactive pitch physics")

st.markdown(
    """
    An educational simulator for baseball pitch trajectories, built around the
    **Magnus effect**, drag, spin axis, active vs gyro spin, and air-density
    sensitivity. Pick a page from the left sidebar to start exploring.

    The URL captures every slider value on the Pitch Playground page, so you
    can share a link to any pitch you build.
    """
)


def _screenshot(name: str, caption: str) -> None:
    """Show a screenshot if available; otherwise a placeholder note."""
    if _SCREENSHOTS_DIR is None:
        return
    path = _SCREENSHOTS_DIR / name
    if path.is_file():
        st.image(str(path), caption=caption, use_container_width=True)
    else:
        st.caption(
            f"📷 _{name}_ — screenshot pending (run `python scripts/capture_screenshots.py` after deploy)"
        )


st.markdown("## What's on each page")

cols = st.columns(2)
with cols[0]:
    st.markdown(
        "### 🎚 Pitch Playground\n"
        "Every slider, every model, animated 3D view of the ball's flight, "
        "full break-metric row, downloadable trajectory CSV / JSON / 3D HTML, "
        "Statcast comparison expander."
    )
    _screenshot("01_playground.png", "Pitch Playground")

    st.markdown(
        "### 🧭 Magnus Explorer\n"
        "The geometry of `ω × v̂`. Three labeled cones at release: velocity, "
        "spin axis, and Magnus break direction. See exactly which way the "
        "Magnus force pushes for any spin axis."
    )
    _screenshot("02_magnus_explorer.png", "Magnus Explorer")

    st.markdown(
        "### ⚖️ Fastball vs Curveball\n"
        "Two pitches side by side, in 3D and from the catcher's view. "
        "Tweak each independently. Strike-zone calls per pitch."
    )
    _screenshot("03_fastball_vs_curveball.png", "Fastball vs Curveball")

with cols[1]:
    st.markdown(
        "### 🎯 Active Spin / Gyro\n"
        "Hold total spin constant, sweep active-spin fraction from 0 to 1. "
        "Watch movement collapse as gyro spin takes over (SPEC §4.4)."
    )
    _screenshot("04_active_spin_gyro.png", "Active Spin / Gyro")

    st.markdown(
        "### 🌬 Drag + Environment\n"
        "Toggle gravity / drag / Magnus, swap atmospheres (sea level / Coors "
        "Field / custom weather), turn on wind. See how each force adds to "
        "the trajectory."
    )
    _screenshot("05_drag_environment.png", "Drag + Environment")

st.markdown(
    """
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
