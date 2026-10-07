"""Suitability screen v0 (engine.siting.suitability) on a synthetic table."""

import numpy as np
import pandas as pd
import pytest

from engine.siting.suitability import (
    Criterion,
    check_weights,
    equal_weights,
    normalize,
    one_at_a_time,
    score,
    weight_sensitivity,
)

CRIT = [
    Criterion("gas", "gas_km", "lower_better"),
    Criterion("cane", "cane_t", "higher_better"),
]


def table():
    return pd.DataFrame(
        {
            "gas_km": [0.0, 50.0, 100.0, 10.0, 5.0],
            "cane_t": [0.0, 100.0, 200.0, 200.0, np.nan],
            "excluded": [False, False, False, True, False],
        },
        index=list("abcde"),
    )


def test_normalize_uses_non_excluded_range_and_direction():
    norm, bounds = normalize(table(), CRIT)
    # gas: range from non-excluded rows 0..100, lower is better
    assert norm.loc["a", "gas"] == 1.0 and norm.loc["c", "gas"] == 0.0
    assert norm.loc["b", "gas"] == pytest.approx(0.5)
    assert norm.loc["c", "cane"] == 1.0 and norm.loc["a", "cane"] == 0.0
    assert bounds.set_index("criterion").loc["gas", "bounds_from"] == "data"


def test_fixed_bounds_clip():
    crit = [Criterion("gas", "gas_km", "lower_better", lo=10, hi=60, note="test")]
    norm, bounds = normalize(table(), crit)
    assert norm.loc["a", "gas"] == 1.0  # below lo
    assert norm.loc["c", "gas"] == 0.0  # above hi
    assert norm.loc["b", "gas"] == pytest.approx(0.2)
    assert bounds.loc[0, "bounds_from"] == "criterion"


def test_score_missing_and_excluded_are_nan():
    t = table()
    norm, _ = normalize(t, CRIT)
    s = score(norm, equal_weights(CRIT), excluded=t["excluded"])
    assert np.isnan(s["d"]) and np.isnan(s["e"])  # excluded; missing cane
    assert s["b"] == pytest.approx(0.5)  # (0.5 + 0.5) / 2
    # zero weight on cane: e is scored on gas alone
    s2 = score(norm, {"gas": 1.0}, excluded=t["excluded"])
    assert s2["e"] == pytest.approx(0.95)


def test_weights_validated():
    with pytest.raises(KeyError):
        check_weights({"nope": 1}, ["gas"])
    with pytest.raises(ValueError):
        check_weights({"gas": -1, "cane": 2}, ["gas", "cane"])
    assert check_weights({"gas": 2, "cane": 2}, ["gas", "cane"]).tolist() == [0.5, 0.5]


def test_weight_sensitivity_dominant_row_is_always_top():
    norm = pd.DataFrame({"gas": [1.0, 0.2, 0.1], "cane": [1.0, 0.3, 0.9]}, index=list("xyz"))
    per_row, draws = weight_sensitivity(norm, n=200, top_k=1, seed=1)
    assert per_row.loc["x", "p_top_k"] == 1.0  # dominates on every criterion
    assert per_row.loc["x", "rank_base"] == 1
    assert draws.shape == (200, 2)
    assert np.allclose(draws.sum(axis=1), 1.0)
    # same seed, same result
    again, _ = weight_sensitivity(norm, n=200, top_k=1, seed=1)
    pd.testing.assert_frame_equal(per_row, again)


def test_one_at_a_time_reports_each_criterion_both_ways():
    norm = pd.DataFrame({"gas": [1.0, 0.0, 0.6], "cane": [0.0, 1.0, 0.6]}, index=list("xyz"))
    out = one_at_a_time(norm, {"gas": 1, "cane": 1}, delta=0.2, top_k=1)
    assert len(out) == 4
    assert set(out["change"]) == {"-20%", "+20%"}
    assert out["top_k_kept"].between(0, 1).all()
