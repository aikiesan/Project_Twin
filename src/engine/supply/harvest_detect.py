"""Harvest-date detection from optical time series (docs/09 §Step 6).

Sugarcane harvest shows up as an abrupt fall of NDVI from a closed canopy to bare soil/straw,
with SWIR reflectance exceeding NIR (dry residue). The rule documented in docs/09 is
"NDVI drops to ≤ ~0.30 with B11 > B8A" — those thresholds are **arguments** here (they come
from the PILAR-2b ``cane_cycle`` prototype and must be validated for each sensor/region).

The functions work on plain arrays, so the same logic runs on:
- per-parcel or per-H3 time series exported from Google Earth Engine
  (``scripts/gee/export_s2_timeseries.py``), or
- local Sentinel-2/Landsat stacks.

Outputs feed :mod:`engine.supply.seasonality` (mill-specific monthly profile) and the mill
activity flag (no harvest in a catchment-year ⇒ probably idle).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class HarvestRule:
    """Thresholds for one harvest event (all REQUIRED; document their origin in the run log).

    Attributes:
        ndvi_high_min: canopy considered closed when NDVI ≥ this before the drop.
        ndvi_low_max: post-harvest when NDVI ≤ this (docs/09 cites ~0.30).
        max_gap_days: the high and the low observation must be at most this far apart
            (longer gaps cannot date the event precisely — flagged instead).
        require_swir_gt_nir: also require B11 > B8A at the low observation.
        min_days_between: minimum spacing between two events at the same unit (ratoon cycle).
    """

    ndvi_high_min: float
    ndvi_low_max: float
    max_gap_days: int
    require_swir_gt_nir: bool
    min_days_between: int


def detect_harvests(
    dates: pd.DatetimeIndex | np.ndarray,
    ndvi: np.ndarray,
    rule: HarvestRule,
    b11: np.ndarray | None = None,
    b8a: np.ndarray | None = None,
) -> pd.DataFrame:
    """Detect harvest events in one unit's time series (NaN = cloud/no data, skipped).

    The event date is the **midpoint** between the last high and the first low valid
    observation; ``uncertainty_days`` is half that interval.

    Returns:
        DataFrame with columns ``date_high``, ``date_low``, ``harvest_date``,
        ``uncertainty_days``, ``ndvi_before``, ``ndvi_after``.
    """
    t = pd.DatetimeIndex(pd.to_datetime(dates))
    v = np.asarray(ndvi, dtype=float)
    if len(t) != len(v):
        raise ValueError("dates and ndvi must have the same length")
    if rule.require_swir_gt_nir and (b11 is None or b8a is None):
        raise ValueError("rule requires b11 and b8a arrays")
    order = np.argsort(t.values)
    t, v = t[order], v[order]
    swir_ok = np.ones(len(v), dtype=bool)
    if rule.require_swir_gt_nir:
        s11 = np.asarray(b11, dtype=float)[order]
        s8a = np.asarray(b8a, dtype=float)[order]
        swir_ok = s11 > s8a
    valid = np.isfinite(v)
    idx = np.flatnonzero(valid)
    events = []
    last_event: pd.Timestamp | None = None
    for a, b in zip(idx[:-1], idx[1:], strict=True):
        if not (v[a] >= rule.ndvi_high_min and v[b] <= rule.ndvi_low_max and swir_ok[b]):
            continue
        gap = (t[b] - t[a]).days
        if gap > rule.max_gap_days:
            continue
        mid = t[a] + (t[b] - t[a]) / 2
        if last_event is not None and (mid - last_event).days < rule.min_days_between:
            continue
        events.append(
            {
                "date_high": t[a],
                "date_low": t[b],
                "harvest_date": mid.normalize(),
                "uncertainty_days": gap / 2,
                "ndvi_before": v[a],
                "ndvi_after": v[b],
            }
        )
        last_event = mid
    return pd.DataFrame(
        events,
        columns=[
            "date_high",
            "date_low",
            "harvest_date",
            "uncertainty_days",
            "ndvi_before",
            "ndvi_after",
        ],
    )


def detect_panel(
    ts: pd.DataFrame,
    rule: HarvestRule,
    unit_col: str = "unit_id",
    date_col: str = "date",
    ndvi_col: str = "ndvi",
    b11_col: str | None = "b11",
    b8a_col: str | None = "b8a",
) -> pd.DataFrame:
    """Apply :func:`detect_harvests` to a long table of many units (parcels / H3 cells)."""
    out = []
    for unit, g in ts.groupby(unit_col, sort=False):
        ev = detect_harvests(
            g[date_col],
            g[ndvi_col].to_numpy(),
            rule,
            g[b11_col].to_numpy() if b11_col and b11_col in g else None,
            g[b8a_col].to_numpy() if b8a_col and b8a_col in g else None,
        )
        if not ev.empty:
            ev.insert(0, unit_col, unit)
            out.append(ev)
    if not out:
        return pd.DataFrame(columns=[unit_col, "harvest_date", "uncertainty_days"])
    return pd.concat(out, ignore_index=True)


def monthly_harvested_area(
    events: pd.DataFrame,
    area_ha: pd.Series,
    group: pd.Series | None = None,
    unit_col: str = "unit_id",
) -> pd.DataFrame:
    """Harvested area (ha) per group (e.g. mill catchment) × month.

    Args:
        events: output of :func:`detect_panel`.
        area_ha: cane area per unit (index = unit id).
        group: group label per unit (index = unit id); ``None`` → single group ``"all"``.

    Returns:
        DataFrame ``group, month (Timestamp month start), harvested_ha, n_units``.
    """
    ev = events[[unit_col, "harvest_date"]].copy()
    ev["harvested_ha"] = ev[unit_col].map(area_ha)
    ev["group"] = ev[unit_col].map(group) if group is not None else "all"
    ev["month"] = pd.to_datetime(ev["harvest_date"]).dt.to_period("M").dt.to_timestamp()
    return (
        ev.groupby(["group", "month"])
        .agg(harvested_ha=("harvested_ha", "sum"), n_units=(unit_col, "nunique"))
        .reset_index()
    )


def monthly_shares(monthly: pd.DataFrame, season_start_month: int) -> pd.DataFrame:
    """Normalise harvested area to shares per group and season (season starts at given month).

    ``season_start_month`` is a project convention (e.g. 4 for an April–March safra) — pass it.
    """
    df = monthly.copy()
    m = df["month"].dt.month
    y = df["month"].dt.year
    df["season"] = np.where(m >= season_start_month, y, y - 1)
    tot = df.groupby(["group", "season"])["harvested_ha"].transform("sum")
    df["share"] = df["harvested_ha"] / tot
    return df


def activity_flags(
    events: pd.DataFrame,
    group: pd.Series,
    seasons: list[int],
    season_start_month: int,
    min_units: int,
    unit_col: str = "unit_id",
) -> pd.DataFrame:
    """Mill activity proxy: a catchment is 'active' in a season if ≥ ``min_units`` harvested.

    Returns a wide boolean table group × season. Use as evidence, not proof (cane may be sent to
    a neighbouring mill — combine with Huff allocation and registries).
    """
    ev = events[[unit_col, "harvest_date"]].copy()
    ev["group"] = ev[unit_col].map(group)
    d = pd.to_datetime(ev["harvest_date"])
    ev["season"] = np.where(d.dt.month >= season_start_month, d.dt.year, d.dt.year - 1)
    counts = ev.groupby(["group", "season"])[unit_col].nunique().unstack(fill_value=0)
    counts = counts.reindex(index=sorted(group.dropna().unique()), columns=seasons, fill_value=0)
    return counts >= min_units
