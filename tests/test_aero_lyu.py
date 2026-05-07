"""Tests for LyuAeroModel — drag-crisis fidelity, Cl monotonicity,
and Protocol satisfaction.
"""

from __future__ import annotations

import itertools

from pitchphys.aero import AeroModel, LyuAeroModel


def test_lyu_satisfies_aero_model_protocol() -> None:
    assert isinstance(LyuAeroModel(), AeroModel)


def test_lyu_cl_zero_at_zero_S() -> None:
    assert LyuAeroModel().cl(1.5e5, 0.0, {}) == 0.0


def test_lyu_cl_monotone_in_S() -> None:
    m = LyuAeroModel()
    Ss = [0.0, 0.05, 0.1, 0.15, 0.2, 0.25, 0.3, 0.35, 0.4, 0.45, 0.5]
    cls = [m.cl(1.5e5, s, {}) for s in Ss]
    for a, b in itertools.pairwise(cls):
        assert b >= a


def test_lyu_cl_canonical_values() -> None:
    """Spot-check Cl at the four S values Lyu Table 1 reports (seam-averaged)."""
    m = LyuAeroModel()
    # Per Table 1 (Lyu p. 6) seam-averaged C_L:
    # S=0.05: avg of (4-seam=0.15, 2-seam=0.05) = 0.10
    # S=0.10: avg of (0.16, 0.07) = 0.115
    # S=0.15: avg of (0.17, 0.17) = 0.17
    # S=0.20: avg of (0.21, 0.18) = 0.195
    table_points = [
        (0.05, 0.100),
        (0.10, 0.115),
        (0.15, 0.170),
        (0.20, 0.195),
    ]
    for S, expected in table_points:
        cl = m.cl(1.5e5, S, {})
        assert abs(cl - expected) < 0.01, f"S={S}: Cl={cl:.3f}, Lyu Table 1 averaged = {expected}"


def test_lyu_drag_crisis_low_S() -> None:
    """At low S, Cd should drop sharply across Re ≈ 150k.

    From Lyu Fig. 5: C_D(Re=80k, S=0.05) ≈ 0.46; C_D(Re=175k, S=0.05) ≈ 0.32.
    """
    m = LyuAeroModel()
    cd_low_re = m.cd(80e3, 0.05, {})
    cd_high_re = m.cd(175e3, 0.05, {})
    assert cd_low_re > 0.40
    assert cd_high_re < 0.36
    assert cd_low_re - cd_high_re > 0.10


def test_lyu_drag_crisis_disappears_at_high_S() -> None:
    """At S >= 0.15, Cd should be essentially Re-independent in our fit."""
    m = LyuAeroModel()
    cd_low_re = m.cd(80e3, 0.30, {})
    cd_high_re = m.cd(200e3, 0.30, {})
    assert abs(cd_low_re - cd_high_re) < 0.01


def test_lyu_cd_minimum_around_S_0p15() -> None:
    """Cd at Re=144k has a minimum around S=0.15 (Fig. 3 inflection)."""
    m = LyuAeroModel()
    cd_at_0 = m.cd(144e3, 0.0, {})
    cd_at_min = m.cd(144e3, 0.15, {})
    cd_at_high = m.cd(144e3, 0.50, {})
    assert cd_at_min < cd_at_0
    assert cd_at_high > cd_at_min


def test_lyu_cd_at_typical_fastball() -> None:
    """Sanity: Cd at a 90 mph 2400 rpm fastball regime ≈ 0.33-0.36.

    For a 90 mph (40.2 m/s) ball, Re ≈ 1.225 * 40.2 * 0.0732 / 1.81e-5 ≈ 1.99e5.
    For 2400 rpm (251 rad/s), S = 0.0366*251/40.2 = 0.228.
    """
    m = LyuAeroModel()
    cd = m.cd(1.99e5, 0.228, {})
    assert 0.32 < cd < 0.37


def test_lyu_cl_at_typical_fastball() -> None:
    """Cl at S=0.23 (90 mph 2400 rpm) should be roughly 0.21-0.25."""
    cl = LyuAeroModel().cl(1.99e5, 0.228, {})
    assert 0.20 < cl < 0.26


def test_lyu_cd_clamps_negative_S() -> None:
    """Negative S inputs (shouldn't happen in practice) clamp to S=0."""
    m = LyuAeroModel()
    assert m.cd(1.5e5, -0.1, {}) == m.cd(1.5e5, 0.0, {})


def test_lyu_re_correction_extrapolates_safely() -> None:
    """Out-of-grid Re values should give plausible drag (np.interp clamps)."""
    m = LyuAeroModel()
    cd_extreme_low = m.cd(50e3, 0.05, {})
    cd_extreme_high = m.cd(400e3, 0.05, {})
    # Both should be finite, positive, and within physical range
    assert 0.20 < cd_extreme_low < 0.60
    assert 0.20 < cd_extreme_high < 0.60
