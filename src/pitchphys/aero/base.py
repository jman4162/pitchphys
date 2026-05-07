"""AeroModel Protocol and the simple/user-defined implementations.

Force formulas live in :mod:`pitchphys.core.forces`; this module only supplies
the dimensionless coefficients and an optional non-Magnus force hook.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

import numpy as np

if TYPE_CHECKING:
    from pitchphys.core.environment import Environment
    from pitchphys.core.pitch import PitchRelease


@runtime_checkable
class AeroModel(Protocol):
    """Pluggable drag/lift coefficient provider.

    Implementations may use any subset of ``Re``, ``S``, and ``ctx`` keys
    they care about. ``non_magnus_force`` returns a 3-vector (N) for any
    extra force outside gravity/drag/Magnus; v0.1 ships zeros.
    """

    def cd(self, Re: float, S: float, ctx: dict[str, Any]) -> float: ...
    def cl(self, Re: float, S: float, ctx: dict[str, Any]) -> float: ...
    def non_magnus_force(
        self,
        t: float,
        state: np.ndarray,
        pitch: PitchRelease,
        env: Environment,
    ) -> np.ndarray: ...


@dataclass
class ConstantAeroModel:
    """Constant drag and lift coefficients. Useful for analytic tests."""

    cd_value: float = 0.35
    cl_value: float = 0.20

    def cd(self, Re: float, S: float, ctx: dict[str, Any]) -> float:
        return self.cd_value

    def cl(self, Re: float, S: float, ctx: dict[str, Any]) -> float:
        return self.cl_value

    def non_magnus_force(
        self,
        t: float,
        state: np.ndarray,
        pitch: PitchRelease,
        env: Environment,
    ) -> np.ndarray:
        return np.zeros(3)


@dataclass
class UserDefinedAeroModel:
    """Wrap user-supplied callables as an AeroModel."""

    cd_fn: Callable[[float, float, dict[str, Any]], float]
    cl_fn: Callable[[float, float, dict[str, Any]], float]
    force_fn: Callable[[float, np.ndarray, PitchRelease, Environment], np.ndarray] | None = None

    def cd(self, Re: float, S: float, ctx: dict[str, Any]) -> float:
        return float(self.cd_fn(Re, S, ctx))

    def cl(self, Re: float, S: float, ctx: dict[str, Any]) -> float:
        return float(self.cl_fn(Re, S, ctx))

    def non_magnus_force(
        self,
        t: float,
        state: np.ndarray,
        pitch: PitchRelease,
        env: Environment,
    ) -> np.ndarray:
        if self.force_fn is None:
            return np.zeros(3)
        return np.asarray(self.force_fn(t, state, pitch, env), dtype=float)
