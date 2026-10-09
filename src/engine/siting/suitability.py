"""Suitability screen v0: exclusions, normalised criteria, weighted score and weight sensitivity.

docs/12 Step 2, ADR-0016. The screen narrows candidate sites; it does not choose them. The main
siting model ranks sites by explicit cost (LCOB, docs/12 Step 5), not by weights.

Input is one table with one row per candidate (an H3 cell or a mill), already holding:

- one numeric column per criterion, in the unit its name carries (``gas_delivery_point_km``,
  ``cane_t_in_30km``…);
- an optional boolean exclusion column (``excluded``, default name). Excluded rows get no score.

Steps:

1. :func:`normalize` maps each criterion to ``[0, 1]``, 1 = best, linearly between two bounds.
   Bounds are explicit in :class:`Criterion` (``lo``/``hi``) or, when left ``None``, the data
   min/max **of the non-excluded rows** (recorded in the output so a run can be repeated).
2. :func:`score` is the weighted linear combination of the normalised criteria. Weights must be
   non-negative and are rescaled to sum to 1. A row missing any weighted criterion gets ``NaN``
   (never a silent 0).
3. :func:`weight_sensitivity` re-scores under ``n`` random weight vectors drawn from a Dirichlet
   distribution centred on the base weights (equal weights by default) and reports, per row, the
   rank under the base weights, the median and 5-95 % rank, and the share of draws in the top k.
   Rows that stay in the top k under most weightings are robust candidates.
4. :func:`one_at_a_time` raises and lowers each weight by ``delta`` (relative), renormalises, and
   reports how much of the base top k survives.
5. :func:`spaced_selection` turns a ranking of cells into distinct candidate sites: neighbouring
   cells share most of their 30 km catchment, so the raw top k is one cluster, not k sites.

Pure pandas/numpy: geometry work (H3 cells, distances) happens before this module.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd

DIRECTIONS = ("lower_better", "higher_better")


@dataclass(frozen=True)
class Criterion:
    """One suitability criterion.

    Attributes:
        name: short id used for weights (e.g. ``"gas"``).
        column: input column, unit in its name (e.g. ``"gas_delivery_point_km"``).
        direction: ``"lower_better"`` (distances, costs) or ``"higher_better"`` (feedstock).
        lo, hi: values mapped to the worst/best ends. For ``lower_better`` a value ``<= lo``
            scores 1 and ``>= hi`` scores 0; for ``higher_better`` ``<= lo`` scores 0 and
            ``>= hi`` scores 1. ``None`` takes the data min (``lo``) or max (``hi``).
        note: where the bounds come from (a norm, a cost break, or "data range").
    """

    name: str
    column: str
    direction: str
    lo: float | None = None
    hi: float | None = None
    note: str = ""

    def __post_init__(self) -> None:
        if self.direction not in DIRECTIONS:
            raise ValueError(f"{self.name}: direction must be one of {DIRECTIONS}")
        if self.lo is not None and self.hi is not None and not self.lo < self.hi:
            raise ValueError(f"{self.name}: needs lo < hi, got {self.lo}, {self.hi}")


def _bounds(values: pd.Series, c: Criterion) -> tuple[float, float]:
    lo = float(values.min()) if c.lo is None else float(c.lo)
    hi = float(values.max()) if c.hi is None else float(c.hi)
    return lo, hi


NORMALIZATIONS = ("linear", "percentile")


def _percentile(v: pd.Series, ref: pd.Series) -> pd.Series:
    """Mid-rank share of ``ref`` values below each ``v`` (ties count half), in ``[0, 1]``."""
    r = np.sort(ref.to_numpy(float))
    a = v.to_numpy(float)
    below = np.searchsorted(r, a, side="left")
    upto = np.searchsorted(r, a, side="right")
    out = (below + upto) / (2.0 * len(r))
    return pd.Series(np.where(np.isnan(a), np.nan, out), index=v.index)


def normalize(
    df: pd.DataFrame,
    criteria: Sequence[Criterion],
    *,
    exclude_col: str | None = "excluded",
    method: str = "linear",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Normalised criteria in ``[0, 1]`` (1 = best) and the bounds used.

    ``method="linear"`` maps ``lo``..``hi`` to 0..1 (ADR-0016). ``method="percentile"`` gives
    each cell its mid-rank share among the non-excluded cells, so a criterion concentrated in a
    few cells (herds, population) does not leave the rest of the state near 0; ``lo``/``hi``
    are then reported but not used.

    Returns:
        ``(norm, bounds)``: ``norm`` has one column per criterion name, same index as ``df``;
        ``bounds`` has one row per criterion with ``column``, ``direction``, ``lo``, ``hi`` and
        ``bounds_from`` (``"criterion"`` or ``"data"``).
    """
    if method not in NORMALIZATIONS:
        raise ValueError(f"method must be one of {NORMALIZATIONS}, got {method!r}")
    _check_unique(criteria)
    keep = _kept(df, exclude_col)
    norm = {}
    rows = []
    for c in criteria:
        if c.column not in df:
            raise KeyError(f"{c.name}: column {c.column!r} not in the table")
        v = pd.to_numeric(df[c.column], errors="raise").astype(float)
        lo, hi = _bounds(v[keep].dropna(), c)
        if method == "percentile":
            x = _percentile(v, v[keep].dropna())
            if c.direction == "lower_better":
                x = 1 - x
        elif hi == lo:
            x = pd.Series(np.where(v.isna(), np.nan, 1.0), index=df.index)
        else:
            x = ((v - lo) / (hi - lo)).clip(0, 1)
            if c.direction == "lower_better":
                x = 1 - x
        norm[c.name] = x
        rows.append(
            {
                "criterion": c.name,
                "column": c.column,
                "direction": c.direction,
                "lo": lo,
                "hi": hi,
                "bounds_from": "criterion" if c.lo is not None and c.hi is not None else "data",
                "method": method,
                "note": c.note,
            }
        )
    return pd.DataFrame(norm, index=df.index), pd.DataFrame(rows)


def check_weights(weights: Mapping[str, float], names: Sequence[str]) -> pd.Series:
    """Weights as a Series over ``names``, non-negative, rescaled to sum 1.

    Criteria absent from ``weights`` get weight 0; unknown names raise.
    """
    unknown = set(weights) - set(names)
    if unknown:
        raise KeyError(f"weights for unknown criteria: {sorted(unknown)}")
    w = pd.Series({n: float(weights.get(n, 0.0)) for n in names})
    if (w < 0).any() or not np.isfinite(w).all():
        raise ValueError(f"weights must be finite and non-negative, got {w.to_dict()}")
    if w.sum() == 0:
        raise ValueError("at least one weight must be positive")
    return w / w.sum()


def equal_weights(criteria: Sequence[Criterion]) -> dict[str, float]:
    """Equal weight for every criterion (the baseline weighting)."""
    return {c.name: 1.0 / len(criteria) for c in criteria}


def score(
    norm: pd.DataFrame, weights: Mapping[str, float], *, excluded: pd.Series | None = None
) -> pd.Series:
    """Weighted linear combination of normalised criteria, in ``[0, 1]``.

    Rows that are excluded, or miss a criterion with positive weight, get ``NaN``.
    """
    w = check_weights(weights, list(norm.columns))
    used = w[w > 0].index
    s = norm[used].mul(w[used], axis=1).sum(axis=1, min_count=len(used))
    s[norm[used].isna().any(axis=1)] = np.nan
    if excluded is not None:
        s[excluded.reindex(s.index).fillna(False).astype(bool)] = np.nan
    return s.rename("score")


def _rank(s: pd.Series) -> pd.Series:
    """Rank 1 = best; NaN rows stay NaN."""
    return s.rank(ascending=False, method="min")


def weight_sensitivity(
    norm: pd.DataFrame,
    *,
    base_weights: Mapping[str, float] | None = None,
    n: int = 1000,
    concentration: float = 1.0,
    top_k: int = 10,
    seed: int = 0,
    excluded: pd.Series | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Rank stability under random weights (Dirichlet around the base weights).

    Args:
        norm: output of :func:`normalize`.
        base_weights: centre of the draws; equal weights when ``None``.
        n: number of weight vectors.
        concentration: Dirichlet total concentration per criterion. ``1`` with equal base
            weights draws uniformly over all weightings; larger values stay closer to the base.
        top_k: size of the "top" set for ``p_top_k``.
        seed: random seed (recorded by the caller with the run).
        excluded: boolean exclusion mask.

    Returns:
        ``(per_row, draws)``. ``per_row`` (index of ``norm``): ``score_base``, ``rank_base``,
        ``rank_median``, ``rank_p05``, ``rank_p95``, ``p_top_k``. ``draws``: the ``n`` weight
        vectors, one column per criterion.
    """
    if n < 1 or top_k < 1 or concentration <= 0:
        raise ValueError("n and top_k must be >= 1 and concentration > 0")
    names = list(norm.columns)
    base = check_weights(base_weights or {c: 1.0 for c in names}, names)
    if (base == 0).any():
        raise ValueError("Dirichlet draws need every base weight > 0; drop zero-weight criteria")
    alpha = (base * len(names) * concentration).to_numpy()
    rng = np.random.default_rng(seed)
    w = rng.dirichlet(alpha, size=n)

    x = norm.to_numpy(dtype=float)
    ok = ~np.isnan(x).any(axis=1)
    if excluded is not None:
        ok &= ~excluded.reindex(norm.index).fillna(False).astype(bool).to_numpy()
    scores = np.full((n, len(norm)), np.nan)
    scores[:, ok] = w @ x[ok].T
    ranks = pd.DataFrame(scores.T, index=norm.index).rank(ascending=False, method="min")

    s_base = score(norm, base.to_dict(), excluded=excluded)
    per_row = pd.DataFrame(
        {
            "score_base": s_base,
            "rank_base": _rank(s_base),
            "rank_median": ranks.median(axis=1),
            "rank_p05": ranks.quantile(0.05, axis=1),
            "rank_p95": ranks.quantile(0.95, axis=1),
            "p_top_k": (ranks <= top_k).mean(axis=1).where(ok),
        }
    )
    return per_row, pd.DataFrame(w, columns=names)


def one_at_a_time(
    norm: pd.DataFrame,
    weights: Mapping[str, float],
    *,
    delta: float = 0.2,
    top_k: int = 10,
    excluded: pd.Series | None = None,
) -> pd.DataFrame:
    """Share of the base top k kept when one weight moves by ``±delta`` (relative).

    Returns one row per criterion and sign with the perturbed weight and ``top_k_kept``
    (fraction of the base top-k rows still in the top k).
    """
    if not 0 < delta < 1:
        raise ValueError("delta must be in (0, 1)")
    names = list(norm.columns)
    base = check_weights(weights, names)
    top_base = set(_rank(score(norm, base.to_dict(), excluded=excluded)).nsmallest(top_k).index)
    out = []
    for c in names:
        for sign in (-1, 1):
            w = base.copy()
            w[c] *= 1 + sign * delta
            w = w / w.sum()
            top = set(_rank(score(norm, w.to_dict(), excluded=excluded)).nsmallest(top_k).index)
            out.append(
                {
                    "criterion": c,
                    "change": f"{sign * delta:+.0%}",
                    "weight": w[c],
                    "top_k_kept": len(top & top_base) / max(len(top_base), 1),
                }
            )
    return pd.DataFrame(out)


EARTH_RADIUS_KM = 6371.0088  # IUGG mean Earth radius; screening distances only


def spaced_selection(
    lat: Sequence[float],
    lon: Sequence[float],
    order: Sequence[int],
    *,
    min_km: float,
    n: int,
) -> list[int]:
    """Greedy pick of up to ``n`` positions, at least ``min_km`` apart (great circle).

    Args:
        lat, lon: degrees, one entry per candidate.
        order: candidate positions, best first (e.g. by ascending rank); NaN-scored rows left out.
        min_km: minimum spacing between picked candidates, km.
        n: maximum number of picks.

    Returns:
        Picked positions, in ``order``. Each pick is the best candidate not within ``min_km`` of
        a better pick (non-maximum suppression).
    """
    if min_km < 0 or n < 1:
        raise ValueError("min_km must be >= 0 and n >= 1")
    la, lo = np.radians(np.asarray(lat, float)), np.radians(np.asarray(lon, float))
    picked: list[int] = []
    for i in order:
        if picked:
            p = np.asarray(picked)
            a = (
                np.sin((la[p] - la[i]) / 2) ** 2
                + np.cos(la[i]) * np.cos(la[p]) * np.sin((lo[p] - lo[i]) / 2) ** 2
            )
            if (2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))).min() < min_km:
                continue
        picked.append(int(i))
        if len(picked) == n:
            break
    return picked


def _kept(df: pd.DataFrame, exclude_col: str | None) -> pd.Series:
    if exclude_col and exclude_col in df:
        return ~df[exclude_col].fillna(False).astype(bool)
    return pd.Series(True, index=df.index)


def _check_unique(criteria: Sequence[Criterion]) -> None:
    names = [c.name for c in criteria]
    if len(set(names)) != len(names):
        raise ValueError(f"duplicate criterion names: {names}")
