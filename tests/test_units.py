"""Unit conversion tests (SPEC §14.1)."""

from __future__ import annotations

import math

import numpy as np
import pytest

from pitchphys.units import (
    ft_to_m,
    in_to_m,
    m_to_ft,
    m_to_in,
    mph_to_mps,
    mps_to_mph,
    radps_to_rpm,
    rpm_to_radps,
)


def test_mph_to_mps_value() -> None:
    assert mph_to_mps(100.0) == pytest.approx(44.704, rel=1e-9)


def test_mph_to_mps_round_trip() -> None:
    assert mps_to_mph(mph_to_mps(95.0)) == pytest.approx(95.0, rel=1e-12)


def test_rpm_to_radps_value() -> None:
    # 60 rpm = 1 rev/s = 2*pi rad/s
    assert rpm_to_radps(60.0) == pytest.approx(2.0 * math.pi, rel=1e-12)


def test_rpm_round_trip() -> None:
    assert radps_to_rpm(rpm_to_radps(2400.0)) == pytest.approx(2400.0, rel=1e-12)


def test_ft_to_m_value() -> None:
    assert ft_to_m(1.0) == pytest.approx(0.3048, rel=1e-12)


def test_ft_round_trip() -> None:
    assert m_to_ft(ft_to_m(55.0)) == pytest.approx(55.0, rel=1e-12)


def test_in_to_m_value() -> None:
    assert in_to_m(12.0) == pytest.approx(0.3048, rel=1e-12)


def test_in_round_trip() -> None:
    assert m_to_in(in_to_m(18.0)) == pytest.approx(18.0, rel=1e-12)


def test_array_inputs_preserved() -> None:
    arr = np.array([0.0, 50.0, 100.0])
    out = mph_to_mps(arr)
    assert isinstance(out, np.ndarray)
    np.testing.assert_allclose(out, arr * 0.44704)
