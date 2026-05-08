"""Tests for the new app helpers shipped with v0.2.x adoption work.

is_strike, trajectory_to_csv, URL pack/unpack — all pure functions, no
Streamlit imports needed.
"""

from __future__ import annotations

import math

import pytest

from pitchphys._app_helpers import (
    CANONICAL_PITCH_KEYS,
    is_strike,
    pack_url_params,
    trajectory_to_csv,
    unpack_url_params,
)
from pitchphys.coordinates import (
    STRIKE_ZONE_BOTTOM_FT,
    STRIKE_ZONE_HALF_WIDTH_FT,
    STRIKE_ZONE_TOP_FT,
)
from pitchphys.core.simulate import simulate
from pitchphys.presets import four_seam

# ---------- is_strike ----------


def test_is_strike_center_of_zone() -> None:
    assert is_strike(0.0, (STRIKE_ZONE_BOTTOM_FT + STRIKE_ZONE_TOP_FT) / 2)


def test_is_strike_corner_inside() -> None:
    """Just inside each corner counts as a strike."""
    eps = 1e-3
    assert is_strike(STRIKE_ZONE_HALF_WIDTH_FT - eps, STRIKE_ZONE_BOTTOM_FT + eps)
    assert is_strike(-(STRIKE_ZONE_HALF_WIDTH_FT - eps), STRIKE_ZONE_TOP_FT - eps)


def test_is_strike_outside_horizontal() -> None:
    """Crossing the plate plane outside the half-width is a ball."""
    assert not is_strike(STRIKE_ZONE_HALF_WIDTH_FT + 0.01, 2.5)
    assert not is_strike(-(STRIKE_ZONE_HALF_WIDTH_FT + 0.01), 2.5)


def test_is_strike_outside_vertical() -> None:
    """Above or below the zone is a ball."""
    assert not is_strike(0.0, STRIKE_ZONE_BOTTOM_FT - 0.01)
    assert not is_strike(0.0, STRIKE_ZONE_TOP_FT + 0.01)


# ---------- trajectory_to_csv ----------


def test_trajectory_to_csv_has_header_and_data() -> None:
    traj = simulate(four_seam())
    csv = trajectory_to_csv(traj)
    lines = csv.strip().splitlines()
    assert lines[0].startswith("t_s,x_m,y_m,z_m")
    assert lines[0].endswith("F_magnus_N")
    # One header + N data rows
    assert len(lines) == len(traj.time) + 1
    # Data rows have 10 columns
    first_data = lines[1].split(",")
    assert len(first_data) == 10
    # First column (time) is 0 at release
    assert float(first_data[0]) == pytest.approx(0.0, abs=1e-9)


def test_trajectory_to_csv_handles_missing_force() -> None:
    """If a force isn't tracked, that column is filled with nan."""
    traj = simulate(four_seam(), forces=["gravity"], _baselines=False)
    csv = trajectory_to_csv(traj)
    # F_drag and F_magnus columns should be all nan since they weren't simulated
    last_data_line = csv.strip().splitlines()[-1].split(",")
    assert last_data_line[8].lower() == "nan"  # F_drag
    assert last_data_line[9].lower() == "nan"  # F_magnus


# ---------- URL pack / unpack ----------


def test_pack_url_params_round_trip() -> None:
    canonical = {
        "speed_mph": 95.0,
        "spin_rpm": 2400.0,
        "tilt_clock": 1.5,
        "active_spin_fraction": 0.95,
        "release_height_ft": 6.0,
        "release_side_ft": -1.5,
        "throwing_hand": "R",
    }
    packed = pack_url_params(canonical)
    unpacked = unpack_url_params(packed)
    for key in CANONICAL_PITCH_KEYS:
        if key == "throwing_hand":
            assert unpacked[key] == canonical[key]
        else:
            assert math.isclose(float(unpacked[key]), float(canonical[key]), rel_tol=1e-5)


def test_unpack_drops_unknown_keys() -> None:
    raw = {"speed_mph": "92.0", "junk": "ignore_me"}
    out = unpack_url_params(raw)
    assert "junk" not in out
    assert out["speed_mph"] == pytest.approx(92.0)


def test_unpack_drops_invalid_values_silently() -> None:
    raw = {"speed_mph": "not_a_number", "spin_rpm": "2400"}
    out = unpack_url_params(raw)
    assert "speed_mph" not in out
    assert out["spin_rpm"] == pytest.approx(2400.0)


def test_unpack_throwing_hand_is_uppercased() -> None:
    assert unpack_url_params({"throwing_hand": "r"})["throwing_hand"] == "R"
    assert unpack_url_params({"throwing_hand": "L"})["throwing_hand"] == "L"
    # Invalid hand value is dropped
    assert "throwing_hand" not in unpack_url_params({"throwing_hand": "X"})


def test_pack_skips_keys_not_in_canonical() -> None:
    """Keys outside CANONICAL_PITCH_KEYS are not encoded."""
    canonical = {"speed_mph": 95.0, "n_samples": 21}
    packed = pack_url_params(canonical)
    assert "speed_mph" in packed
    assert "n_samples" not in packed
