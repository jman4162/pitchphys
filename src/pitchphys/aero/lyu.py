"""Empirical aerodynamic model fit to Lyu et al. 2022 wind-tunnel data.

Source
------
Lyu, B., Smith, L., Elliott, J., & Kensrud, J. (2022).
"The dependence of baseball lift and drag on spin."
*Proc IMechE Part P: J Sports Engineering and Technology* (DOI 10.1177/17543371221113914).
PDF in this repo: ``references/LyuDragLiftSpin.pdf``.

This is what `model="magnus"` resolves to by default. Compared to the simpler
:class:`SimpleMagnusModel` and Sawicki-bilinear :class:`NathanLiftModel`, this
model captures two real effects:

1. **Drag crisis** — at low spin, ``C_D`` drops from ~0.45 to ~0.32 across
   ``Re ≈ 75k → 175k`` (Fig. 5 of the paper).
2. **Spin-dependent drag** — beyond ``S ≈ 0.15`` the drag crisis is absent
   and ``C_D`` rises roughly linearly with ``S`` (Fig. 3).

Lift is the seam-averaged ``C_L(S)`` from Fig. 3 / Table 1. Two-seam vs
four-seam splits at ``S < 0.15`` are folded in via the average — a true
seam-orientation split is reserved for the v0.3 seam-shifted-wake model.

Implementation: ``np.interp`` on small lookup tables. Each table value is
hand-extracted from the paper's published figures and tagged with its
source.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from pitchphys.core.environment import Environment
    from pitchphys.core.pitch import PitchRelease


# ----- Lookup tables -------------------------------------------------------
# Lyu et al. 2022 Fig. 3 (Re ≈ 144k), seam-orientation-averaged C_D and C_L
# vs spin factor S. Values eyeballed from the published chart with
# Table 1 (p. 6) used to anchor S = 0.05, 0.10, 0.15, 0.20.

_S_GRID = np.array([0.00, 0.05, 0.10, 0.15, 0.20, 0.25, 0.30, 0.35, 0.40, 0.45, 0.50])
# C_D at Re ≈ 144k vs S (Fig. 3, mean of 2-seam and 4-seam markers).
# Drag falls slightly across S < 0.15, then climbs roughly linearly.
_CD_AT_REF_RE = np.array([0.35, 0.34, 0.32, 0.32, 0.33, 0.34, 0.36, 0.38, 0.39, 0.41, 0.42])
# C_L vs S (Fig. 3 + Table 1, seam-averaged).
# Below S = 0.15 the four-seam axis dominates the average; above S = 0.15
# the two orientations converge.
_CL_VS_S = np.array([0.00, 0.10, 0.115, 0.17, 0.195, 0.230, 0.270, 0.305, 0.340, 0.385, 0.400])

# Lyu Fig. 5: C_D vs Re at S = 0.05, capturing the drag crisis.
# Eyeballed from chart; smooth Re_crit ≈ 150 k.
_RE_GRID = np.array([75e3, 100e3, 125e3, 150e3, 175e3, 200e3, 250e3])
_CD_AT_S0P05_VS_RE = np.array([0.46, 0.44, 0.42, 0.36, 0.32, 0.34, 0.35])

# Re correction factor = C_D(Re, S=0.05) / C_D(Re=144k, S=0.05).
# At Re ≈ 144k this is ~1.0; at low Re it's ~1.35; past the crisis it dips
# below 1.0. The reference value 0.34 matches `_CD_AT_REF_RE[1]` (S=0.05).
_CD_S0P05_REFERENCE = 0.34
_RE_CORRECTION = _CD_AT_S0P05_VS_RE / _CD_S0P05_REFERENCE

# The Re correction is meaningful only at low S; above S ≈ 0.15 the drag
# crisis disappears (see paper Figs. 3, 5 discussion). We hold the
# correction at full strength up to S = 0.05 (where Lyu measured the
# crisis) and fade it linearly to zero at S = 0.15.
_RE_BLEND_S_FULL = 0.05
_RE_BLEND_S_MAX = 0.15


@dataclass
class LyuAeroModel:
    """Lyu 2022 wind-tunnel ``C_D(Re, S)`` and ``C_L(S)`` (seam-averaged).

    Default for ``model="magnus"``. See module docstring for sourcing.
    """

    def cd(self, Re: float, S: float, ctx: dict[str, Any]) -> float:
        S_clamped = max(0.0, S)
        cd_base = float(np.interp(S_clamped, _S_GRID, _CD_AT_REF_RE))
        if S_clamped >= _RE_BLEND_S_MAX:
            return cd_base
        re_factor = float(np.interp(Re, _RE_GRID, _RE_CORRECTION))
        if S_clamped <= _RE_BLEND_S_FULL:
            blend = 1.0
        else:
            blend = (_RE_BLEND_S_MAX - S_clamped) / (_RE_BLEND_S_MAX - _RE_BLEND_S_FULL)
        return cd_base * (1.0 + blend * (re_factor - 1.0))

    def cl(self, Re: float, S: float, ctx: dict[str, Any]) -> float:
        if S <= 0.0:
            return 0.0
        return float(np.interp(S, _S_GRID, _CL_VS_S))

    def non_magnus_force(
        self,
        t: float,
        state: np.ndarray,
        pitch: PitchRelease,
        env: Environment,
    ) -> np.ndarray:
        return np.zeros(3)
