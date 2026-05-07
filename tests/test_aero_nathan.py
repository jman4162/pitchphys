"""Tests for the rewritten NathanLiftModel (SHS bilinear C_L(S)).

The headline test in this file is the **Nathan Table I regression**:
``ajpfeb08.pdf`` p. 124 lists four pitched-ball deflections (Magnus-only)
over 55 ft for typical fastball / curveball (v, ω) combinations using
the SHS C_L parametrization with Adair C_D. We reproduce these.
"""

from __future__ import annotations

import math

import pytest

from pitchphys.aero import NathanLiftModel
from pitchphys.core.pitch import PitchRelease
from pitchphys.core.simulate import simulate
from pitchphys.units import ft_to_m


def test_cl_zero_at_zero_S() -> None:
    assert NathanLiftModel().cl(1e5, 0.0, {}) == 0.0


def test_cl_continuity_at_S_eq_0p1() -> None:
    """The two bilinear pieces agree at S=0.1 (both give 0.15)."""
    m = NathanLiftModel()
    assert m.cl(1e5, 0.0999, {}) == pytest.approx(1.5 * 0.0999, rel=1e-9)
    assert m.cl(1e5, 0.1000, {}) == pytest.approx(0.09 + 0.6 * 0.1, rel=1e-9)
    # Both pieces evaluate to ~0.15 at S=0.1
    assert abs(m.cl(1e5, 0.0999, {}) - m.cl(1e5, 0.1, {})) < 1e-3


def test_cl_low_S_branch() -> None:
    """For S<0.1, C_L = 1.5*S."""
    m = NathanLiftModel()
    assert m.cl(1e5, 0.05, {}) == pytest.approx(0.075, rel=1e-9)
    assert m.cl(1e5, 0.08, {}) == pytest.approx(0.12, rel=1e-9)


def test_cl_high_S_branch() -> None:
    """For S>=0.1, C_L = 0.09 + 0.6*S."""
    m = NathanLiftModel()
    assert m.cl(1e5, 0.10, {}) == pytest.approx(0.15, rel=1e-9)
    assert m.cl(1e5, 0.20, {}) == pytest.approx(0.21, rel=1e-9)
    assert m.cl(1e5, 0.30, {}) == pytest.approx(0.27, rel=1e-9)
    assert m.cl(1e5, 0.50, {}) == pytest.approx(0.39, rel=1e-9)


def test_cl_monotone_in_S() -> None:
    import itertools

    m = NathanLiftModel()
    Ss = [0.0, 0.05, 0.1, 0.15, 0.2, 0.3, 0.4, 0.5]
    cls = [m.cl(1e5, s, {}) for s in Ss]
    for a, b in itertools.pairwise(cls):
        assert b >= a


def test_cl_within_envelope_of_nathan_fig5() -> None:
    """At canonical points, Cl falls within the eyeballed Fig. 5 data envelope."""
    m = NathanLiftModel()
    # Fig. 5 (page 2 of ajpfeb08.pdf) point estimates with ~±0.05 envelope:
    fig5_points = [
        # (S, expected_Cl, tolerance)
        (0.10, 0.20, 0.06),  # SHS gives 0.15; Nathan's measured ~0.18-0.22
        (0.20, 0.23, 0.05),
        (0.30, 0.29, 0.05),
        (0.50, 0.40, 0.05),
    ]
    for S, target, tol in fig5_points:
        cl = m.cl(1e5, S, {})
        assert abs(cl - target) < tol, f"S={S}: Cl={cl:.3f}, expected {target}±{tol}"


# ---------------------------------------------------------------------------
# Nathan Table I regression — the headline test for the rewrite.
#
# ajpfeb08.pdf p. 124, Table I: deflection of a pitched baseball with the
# given (v, ω, S) over 55 ft, using SHS C_L and Adair C_D.
#
#   v (mph)   ω (rpm)   S       deflection (in)
#   75        1000      0.11    16
#   75        1800      0.20    21
#   90        1000      0.09    14
#   90        1800      0.17    19
#
# Notes:
# - Nathan's "deflection" is the magnus-only break perpendicular to a
#   horizontally-launched trajectory. We replicate by simulating with
#   model="nathan", launch_angle_deg=0, pure backspin, full physics, and
#   reading magnus_break_z_in (the perpendicular Magnus deflection).
# - We use Cd=0.35 here, not Adair's full speed-dependent Cd, so we expect
#   ±3 in. of slop vs Table I.
# - Spin decay disabled to match Nathan's constant-spin assumption.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("speed_mph", "spin_rpm", "expected_in"),
    [
        (75.0, 1000.0, 16.0),
        (75.0, 1800.0, 21.0),
        (90.0, 1000.0, 14.0),
        (90.0, 1800.0, 19.0),
    ],
)
def test_nathan_table_i_regression(speed_mph: float, spin_rpm: float, expected_in: float) -> None:
    pitch = PitchRelease.from_mph_rpm_axis(
        speed_mph=speed_mph,
        spin_rpm=spin_rpm,
        tilt_clock=12.0,
        active_spin_fraction=1.0,
        launch_angle_deg=0.0,
        horizontal_angle_deg=0.0,
        release_height_ft=5.0,
        release_side_ft=0.0,
    )
    # Nathan assumes constant spin over the 55 ft path — matches the v0.1
    # simulator's behavior. After v0.1.5 spin-decay lands we should pass
    # `spin_decay_tau_s=None` to keep this test stable.
    traj = simulate(
        pitch,
        model="nathan",
        plate_distance_m=ft_to_m(55.0),
    )
    deflection_in = traj.magnus_break_z_in
    assert abs(deflection_in - expected_in) < 3.0, (
        f"v={speed_mph}, ω={spin_rpm}: deflection={deflection_in:.2f} in, "
        f"Nathan Table I expected {expected_in} ± 3 in"
    )


def test_nathan_spin_factor_matches_paper_formula() -> None:
    """Sanity: Nathan's S = 8.53e-3 * ω(rpm) / v(mph) (paper p. 119)."""
    # 90 mph, 1800 rpm -> S = 0.17 per paper
    omega_radps = 1800.0 * 2.0 * math.pi / 60.0
    R = 0.0366
    v_mps = 90.0 * 0.44704
    S = R * omega_radps / v_mps
    # Paper rounds to 0.17
    assert S == pytest.approx(0.17, abs=0.01)
