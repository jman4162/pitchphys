"""Tests for AeroModel implementations."""

from __future__ import annotations

import itertools

import numpy as np
import pytest

from pitchphys.aero import (
    AeroModel,
    ConstantAeroModel,
    NathanLiftModel,
    SimpleMagnusModel,
    UserDefinedAeroModel,
)


def test_constant_returns_constants() -> None:
    m = ConstantAeroModel(cd_value=0.42, cl_value=0.13)
    assert m.cd(1e5, 0.2, {}) == 0.42
    assert m.cl(1e5, 0.2, {}) == 0.13


def test_simple_magnus_zero_S_zero_cl() -> None:
    m = SimpleMagnusModel()
    assert m.cl(1e5, 0.0, {}) == 0.0


def test_simple_magnus_caps_at_cl_max() -> None:
    m = SimpleMagnusModel(a=1.0, cl_max=0.4)
    assert m.cl(1e5, 100.0, {}) == 0.4  # huge S clamped
    assert m.cl(1e5, 0.2, {}) == pytest.approx(0.2, rel=1e-9)


def test_nathan_lift_zero_at_zero_S() -> None:
    m = NathanLiftModel()
    assert m.cl(1e5, 0.0, {}) == 0.0


def test_nathan_lift_monotone_in_S() -> None:
    m = NathanLiftModel()
    Ss = [0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5]
    cls = [m.cl(1e5, S, {}) for S in Ss]
    for a, b in itertools.pairwise(cls):
        assert b > a


def test_user_defined_dispatches() -> None:
    calls: list[tuple[str, float, float]] = []

    def cd(Re: float, S: float, ctx: dict[str, object]) -> float:
        calls.append(("cd", Re, S))
        return 0.4

    def cl(Re: float, S: float, ctx: dict[str, object]) -> float:
        calls.append(("cl", Re, S))
        return 0.25

    m = UserDefinedAeroModel(cd_fn=cd, cl_fn=cl)
    assert m.cd(1.0, 0.2, {}) == 0.4
    assert m.cl(1.0, 0.2, {}) == 0.25
    assert len(calls) == 2


def test_user_defined_force_default_zero() -> None:
    m = UserDefinedAeroModel(cd_fn=lambda *_: 0.3, cl_fn=lambda *_: 0.2)
    f = m.non_magnus_force(0.0, np.zeros(6), pitch=None, env=None)  # type: ignore[arg-type]
    np.testing.assert_allclose(f, np.zeros(3))


def test_aero_model_protocol_runtime_check() -> None:
    # Structural typing — concrete classes should satisfy the protocol.
    assert isinstance(ConstantAeroModel(), AeroModel)
    assert isinstance(SimpleMagnusModel(), AeroModel)
    assert isinstance(NathanLiftModel(), AeroModel)
