"""Built-in lift / Magnus coefficient models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from pitchphys.core.environment import Environment
    from pitchphys.core.pitch import PitchRelease


@dataclass
class SimpleMagnusModel:
    """Simple linear-in-spin-factor lift model: ``Cl = min(a * S, cl_max)``.

    Default for ``model="magnus"``. Transparent and pedagogically clear; not
    a precise empirical fit.
    """

    cd_value: float = 0.35
    a: float = 1.0
    cl_max: float = 0.4

    def cd(self, Re: float, S: float, ctx: dict[str, Any]) -> float:
        return self.cd_value

    def cl(self, Re: float, S: float, ctx: dict[str, Any]) -> float:
        return min(self.a * S, self.cl_max)

    def non_magnus_force(
        self,
        t: float,
        state: np.ndarray,
        pitch: PitchRelease,
        env: Environment,
    ) -> np.ndarray:
        return np.zeros(3)


@dataclass
class NathanLiftModel:
    """Lift model from Nathan 2008 — the Sawicki, Hubbard, Stronge (2003) bilinear.

    Implements the Sawicki-Hubbard-Stronge (SHS) bilinear ``C_L(S)``:

        C_L = 1.5 * S            for S <  0.1
        C_L = 0.09 + 0.6 * S     for S >= 0.1

    where ``S = R * |omega_perp| / |v_rel|`` is the dimensionless spin factor.
    The two pieces agree at ``S = 0.1`` (both give ``C_L = 0.15``), so the
    function is continuous.

    Nathan's 2008 motion-capture experiment (Am. J. Phys. 76:119-124)
    independently measured C_L over ``v = 50-110 mph`` and ``S = 0.1-0.6``,
    finding "excellent agreement with the SHS parametrization for S < 0.3."
    See ``references/ajpfeb08.pdf`` Sec. IV.A and Fig. 5; the explicit
    formula appears as Eq. (2) of Nathan's arXiv preprint physics/0605041.

    Drag is held at a constant ``C_D = 0.35``. Nathan 2008 Fig. 4 shows
    the actual ``C_D`` has a weak speed dependence and considerable
    scatter; for a Re- and spin-dependent drag use ``LyuAeroModel``.

    History: v0.1 of this package implemented ``C_L = 1.5*S/(0.4 + 2.32*S)``
    in this class — that rational fit was misattributed to Nathan 2008 and
    has been replaced (v0.1.5) with the actual SHS bilinear.
    """

    cd_value: float = 0.35

    def cd(self, Re: float, S: float, ctx: dict[str, Any]) -> float:
        return self.cd_value

    def cl(self, Re: float, S: float, ctx: dict[str, Any]) -> float:
        if S <= 0.0:
            return 0.0
        if S < 0.1:
            return 1.5 * S
        return 0.09 + 0.6 * S

    def non_magnus_force(
        self,
        t: float,
        state: np.ndarray,
        pitch: PitchRelease,
        env: Environment,
    ) -> np.ndarray:
        return np.zeros(3)
