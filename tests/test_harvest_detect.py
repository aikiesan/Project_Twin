"""Tests for harvest detection on SYNTHETIC NDVI series (thresholds are test values)."""

import numpy as np
import pandas as pd
import pytest

from engine.supply.harvest_detect import (
    HarvestRule,
    activity_flags,
    detect_harvests,
    detect_panel,
    monthly_harvested_area,
    monthly_shares,
)

RULE = HarvestRule(
    ndvi_high_min=0.6,
    ndvi_low_max=0.3,
    max_gap_days=30,
    require_swir_gt_nir=True,
    min_days_between=180,
)


def _series(harvest_idx: int, n: int = 40, step: int = 5, start="2025-04-01"):
    dates = pd.date_range(start, periods=n, freq=f"{step}D")
    ndvi = np.full(n, 0.8)
    ndvi[harvest_idx:] = 0.2
    ndvi[harvest_idx + 6 :] = np.linspace(0.3, 0.7, n - harvest_idx - 6)  # regrowth
    b11 = np.where(ndvi <= 0.3, 0.30, 0.15)
    b8a = np.where(ndvi <= 0.3, 0.25, 0.35)
    return dates, ndvi, b11, b8a


def test_single_event_midpoint_and_uncertainty():
    dates, ndvi, b11, b8a = _series(harvest_idx=10)
    ev = detect_harvests(dates, ndvi, RULE, b11, b8a)
    assert len(ev) == 1
    # last high on day 45 (2025-05-16), first low on day 50 (2025-05-21) → midpoint 2025-05-18
    assert ev.loc[0, "harvest_date"] == pd.Timestamp("2025-05-18")
    assert ev.loc[0, "uncertainty_days"] == pytest.approx(2.5)


def test_clouds_widen_gap_and_long_gap_rejected():
    dates, ndvi, b11, b8a = _series(harvest_idx=10)
    ndvi = ndvi.copy()
    ndvi[7:10] = np.nan  # clouds before the drop → gap 20 d (still ≤ 30)
    ev = detect_harvests(dates, ndvi, RULE, b11, b8a)
    assert ev.loc[0, "uncertainty_days"] == pytest.approx(10.0)
    ndvi[3:10] = np.nan  # gap 40 d > 30 → cannot date → no event
    assert detect_harvests(dates, ndvi, RULE, b11, b8a).empty


def test_swir_condition_blocks_false_positive():
    dates, ndvi, b11, b8a = _series(harvest_idx=10)
    b11 = np.full_like(b11, 0.1)  # SWIR never above NIR (e.g. flooding/cloud shadow)
    assert detect_harvests(dates, ndvi, RULE, b11, b8a).empty
    with pytest.raises(ValueError):
        detect_harvests(dates, ndvi, RULE)  # rule needs SWIR bands


def test_panel_monthly_area_shares_and_activity():
    rows = []
    for unit, hidx in (("a", 10), ("b", 16), ("c", 30)):
        dates, ndvi, b11, b8a = _series(hidx)
        rows.append(
            pd.DataFrame({"unit_id": unit, "date": dates, "ndvi": ndvi, "b11": b11, "b8a": b8a})
        )
    ts = pd.concat(rows)
    ev = detect_panel(ts, RULE)
    assert set(ev["unit_id"]) == {"a", "b", "c"}
    area = pd.Series({"a": 10.0, "b": 30.0, "c": 60.0})
    grp = pd.Series({"a": "mill1", "b": "mill1", "c": "mill1"})
    m = monthly_harvested_area(ev, area, grp)
    # a: 2025-05-18 (May), b: idx16 → days 75/80 → 2025-06-17 (Jun), c: idx30 → 2025-08-16 (Aug)
    got = dict(zip(m["month"].dt.month, m["harvested_ha"], strict=True))
    assert got == {5: 10.0, 6: 30.0, 8: 60.0}
    sh = monthly_shares(m, season_start_month=4)
    assert sh["share"].sum() == pytest.approx(1.0)
    flags = activity_flags(ev, grp, [2024, 2025], season_start_month=4, min_units=2)
    assert bool(flags.loc["mill1", 2025]) and not bool(flags.loc["mill1", 2024])
