"""Greedy hub coverage with a minimum scale: how many hubs, and where (docs/12 Step 1, ADR-0018).

Port of the hub selection of the ESD "FL espacial" (``fl_comum.cobertura_gulosa``, variant B),
built on the maximal covering location problem of Church & ReVelle 1974 (references.csv
``church1974``). The port follows the method as described in ``docs/inbox/esd_inventory.md`` §2
M1; the ESD code stays on the user's PC, so results are not claimed to match the ESD outputs
(``mclp.csv``) until compared there.

Supply sits at sources ``i`` (e.g. Nm³ CH₄/d of N3 per cell or facility; any additive unit) and
hubs can open at candidates ``j``. A source at road distance ``d`` from a hub counts with

    w(d) = 1 for d <= r1,  (r2 - d) / (r2 - r1) for r1 < d < r2,  0 for d >= r2,

with ``r1`` and ``r2`` set per material class (liquid, wet solid, dry solid); ``r1 == r2`` is the
binary coverage radius of the MCLP. Rules (ADR-0018):

- Each source counts once, at its best open hub: covered(S) = sum_i s_i * max_{j in S} w_ij. Ties
  go to the hub opened first.
- A hub opens only if it adds at least ``q_min`` to the covered supply. At each step the greedy
  opens the hub that adds most. What a hub adds can only shrink as others open, so gains are
  re-evaluated lazily and the run stops for good once the best one is below ``q_min``.
- Existing plants can be opened first (``fixed``), whatever they add.
- With ``r1 < r2`` a later hub can take nearer sources from an earlier one and leave it below
  ``q_min``. With ``prune=True`` such hubs are closed, smallest first, and their sources move to
  their next-best open hub, so every hub left (fixed ones aside) collects at least ``q_min``.

The greedy is a heuristic: it can miss the best set of hubs (see the tests) and it depends on the
candidate grid. It narrows candidates and gives the coverage curve (hubs needed for a share of the
supply); the cost model (docs/12 Step 5) decides.

Distances are road distances supplied by the caller (CLAUDE.md): routed
(:func:`engine.siting.routing.od_matrix`, then :func:`pairs_from_dense`) or, where explicitly
allowed, great-circle distance times a cited detour factor (:func:`sphere_xyz_m` and
:func:`fallback_pairs_km`, the rule of :func:`engine.siting.routing.fallback_road_km`). The radii
and ``q_min`` have no defaults: no sourced value exists yet (docs/21 Q20, Q23).
"""

from __future__ import annotations

import heapq
import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import sparse
from scipy.spatial import cKDTree

from engine.siting.routing import EARTH_RADIUS_KM


def decay_weight(d_km: np.ndarray | float, r1_km: np.ndarray | float, r2_km: np.ndarray | float):
    """Distance-decay weight w(d): 1 up to ``r1_km``, linear down to 0 at ``r2_km``, 0 beyond.

    Arguments broadcast; distances and radii in km. ``r1_km == r2_km`` gives a step (binary
    coverage radius). A NaN distance (unreachable pair) gives 0.

    Raises:
        ValueError: on a negative distance, a negative or non-finite radius, or ``r1 > r2``.
    """
    d = np.asarray(d_km, float)
    r1 = np.asarray(r1_km, float)
    r2 = np.asarray(r2_km, float)
    if not (np.all(np.isfinite(r1)) and np.all(np.isfinite(r2))):
        raise ValueError("radii must be finite")
    if np.any(d < 0) or np.any(r1 < 0) or np.any(r2 < r1):
        raise ValueError("need d_km >= 0 and 0 <= r1_km <= r2_km")
    span = r2 - r1
    with np.errstate(divide="ignore", invalid="ignore"):
        ramp = np.where(span > 0, (r2 - d) / span, 0.0)
    return np.where(d <= r1, 1.0, np.where(d < r2, ramp, 0.0))


def sphere_xyz_m(lat_deg: np.ndarray, lon_deg: np.ndarray) -> np.ndarray:
    """(n, 3) positions in metres on a sphere of radius ``EARTH_RADIUS_KM`` (routing.py).

    The straight-line (chord) distance between two such points is the great-circle distance
    ``s`` of :func:`engine.siting.routing.haversine_km` times sin(x)/x, x = s / 2R: shorter by
    less than 4e-6 (relative) up to 60 km. Pass them to :func:`fallback_pairs_km` so that the
    detour factor multiplies the distance it was measured against (``road_detour_factor_*``:
    road km per great-circle km as registered; the ESD denominator may be the EPSG:5880 straight
    line, docs/21 Q24).
    """
    lat = np.radians(np.asarray(lat_deg, float))
    lon = np.radians(np.asarray(lon_deg, float))
    if lat.shape != lon.shape:
        raise ValueError("lat_deg and lon_deg must have the same shape")
    r = EARTH_RADIUS_KM * 1000.0
    xyz = [r * np.cos(lat) * np.cos(lon), r * np.cos(lat) * np.sin(lon), r * np.sin(lat)]
    return np.stack(xyz, axis=-1).reshape(-1, 3)


def _points_m(a, name: str) -> np.ndarray:
    a = np.asarray(a, float)
    if a.ndim == 1 and a.size == 0:
        a = a.reshape(0, 2)
    if a.ndim != 2 or a.shape[1] not in (2, 3):
        raise ValueError(f"{name}: expected an (n, 2) or (n, 3) array of metres")
    return a


def fallback_pairs_km(
    src_m: np.ndarray,
    cand_m: np.ndarray,
    *,
    max_road_km: float,
    detour_factor: float,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Source-candidate pairs within ``max_road_km``, road distance = straight line × detour.

    Only where no routed distance exists and the run log cites the factor (SP medians by distance
    band: ``road_detour_factor_*`` in parameters.csv, flag D, road km per great-circle km).

    Args:
        src_m, cand_m: (n, k) and (m, k) positions in metres: :func:`sphere_xyz_m` (k = 3,
            great-circle distances, the basis of the detour factors) or one projected CRS
            (k = 2, plane distances, which carry the projection's scale error).
        max_road_km: largest road distance kept (km), usually the largest ``r2``.
        detour_factor: road km per straight-line km, >= 1.

    Returns:
        ``(i, j, road_km)``: source positions, candidate positions, estimated road distances.
    """
    if not detour_factor >= 1.0:
        raise ValueError("detour_factor must be >= 1 (road distance cannot beat a straight line)")
    if not max_road_km >= 0:
        raise ValueError("max_road_km must be >= 0")
    a = _points_m(src_m, "src_m")
    b = _points_m(cand_m, "cand_m")
    if a.shape[1] != b.shape[1]:
        raise ValueError("src_m and cand_m must have the same number of coordinates")
    r = cKDTree(a).sparse_distance_matrix(
        cKDTree(b), max_distance=max_road_km * 1000.0 / detour_factor, output_type="ndarray"
    )
    return r["i"].astype(np.int64), r["j"].astype(np.int64), r["v"] / 1000.0 * detour_factor


def pairs_from_dense(
    dist_km: np.ndarray, max_km: float
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """``(i, j, d)`` for the finite entries ``<= max_km`` of a dense matrix (e.g. OSRM output)."""
    d = np.asarray(dist_km, float)
    i, j = np.nonzero(np.isfinite(d) & (d <= max_km))
    return i.astype(np.int64), j.astype(np.int64), d[i, j]


def weight_matrix(
    i: np.ndarray,
    j: np.ndarray,
    d_km: np.ndarray,
    r1_km: np.ndarray | float,
    r2_km: np.ndarray | float,
    shape: tuple[int, int],
) -> sparse.csc_array:
    """Sparse (sources × candidates) matrix of decay weights from distance triplets.

    Args:
        i, j, d_km: source position, candidate position and road distance (km) of each pair.
        r1_km, r2_km: radii (km), scalars or one value per source (its material class).
        shape: ``(n_sources, n_candidates)``.

    Returns:
        CSC matrix holding the pairs with weight > 0.

    Raises:
        ValueError: on lengths that differ, positions out of range, or a repeated pair with
            weight > 0.
    """
    i = np.asarray(i, np.int64)
    j = np.asarray(j, np.int64)
    d = np.asarray(d_km, float)
    n, m = shape
    if not len(i) == len(j) == len(d):
        raise ValueError("i, j and d_km must have the same length")
    if len(i) and (i.min() < 0 or i.max() >= n or j.min() < 0 or j.max() >= m):
        raise ValueError("pair position out of range for shape")
    r1 = np.asarray(r1_km, float)
    r2 = np.asarray(r2_km, float)
    w = decay_weight(d, r1[i] if r1.ndim else r1, r2[i] if r2.ndim else r2)
    keep = w > 0
    out = sparse.csc_array((w[keep], (i[keep], j[keep])), shape=(n, m))
    if out.nnz != int(keep.sum()):  # the conversion summed a repeated pair
        raise ValueError("repeated (source, candidate) pair")
    out.sort_indices()
    return out


def fallback_weight_matrix(
    src_m: np.ndarray,
    cand_m: np.ndarray,
    r1_km: np.ndarray | float,
    r2_km: np.ndarray | float,
    *,
    detour_factor: float,
    keep_pair: Callable[[np.ndarray, np.ndarray], np.ndarray] | None = None,
    chunk: int = 4096,
) -> sparse.csc_array:
    """:func:`weight_matrix` over :func:`fallback_pairs_km`, built in chunks of candidates.

    Args:
        src_m, cand_m: (n, k) and (m, k) positions in metres (:func:`fallback_pairs_km`).
        r1_km, r2_km: radii (km), scalars or one value per source.
        detour_factor: road km per straight-line km, >= 1, cited in the run log.
        keep_pair: optional ``f(i, j) -> bool mask`` on source and candidate positions; pairs
            it rejects get no weight (e.g. straw only to mills).
        chunk: candidates per chunk; bounds the memory held by the distance pairs.
    """
    src = _points_m(src_m, "src_m")
    cand = _points_m(cand_m, "cand_m")
    n, m = len(src), len(cand)
    r1 = np.asarray(r1_km, float)
    r2 = np.asarray(r2_km, float)
    blocks = []
    for c0 in range(0, m, chunk):
        part = cand[c0 : c0 + chunk]
        i, j, d = fallback_pairs_km(
            src, part, max_road_km=float(r2.max()) if r2.size else 0.0, detour_factor=detour_factor
        )
        if keep_pair is not None:
            k = np.asarray(keep_pair(i, j + c0), bool)
            i, j, d = i[k], j[k], d[k]
        blocks.append(weight_matrix(i, j, d, r1, r2, (n, len(part))))
    if not blocks:
        return sparse.csc_array((n, 0))
    out = sparse.csc_array(sparse.hstack(blocks, format="csc"))
    out.sort_indices()
    return out


@dataclass(frozen=True)
class Coverage:
    """Result of :func:`greedy_coverage`.

    Attributes:
        trace: one row per hub in opening order: ``step``, ``hub`` (candidate position),
            ``fixed``, ``gain`` (supply it added), ``covered`` and ``covered_share`` after it.
        hubs: one row per opened hub: ``hub``, ``step``, ``fixed``, ``gain_at_entry``,
            ``closed`` (pruned), ``supply_allocated`` and ``n_sources`` after allocation and
            pruning, ``meets_qmin``.
        owner: per source, the candidate position of its hub (-1 if uncovered).
        weight: per source, its weight at that hub (0 if uncovered).
        total_supply: sum of the supply.
        covered: supply collected by the final hubs (sum of ``supply_allocated``).
        covered_greedy: supply covered when the greedy stopped, before pruning.
        q_min: the minimum scale used.
        stop_reason: ``q_min``, ``max_hubs``, ``target_share`` or ``exhausted``.
    """

    trace: pd.DataFrame
    hubs: pd.DataFrame
    owner: np.ndarray
    weight: np.ndarray
    total_supply: float
    covered: float
    covered_greedy: float
    q_min: float
    stop_reason: str

    @property
    def covered_share(self) -> float:
        """Share of the supply collected by the final hubs (NaN if there is no supply)."""
        return self.covered / self.total_supply if self.total_supply > 0 else math.nan


def _as_csc(weights) -> sparse.csc_array:
    W = sparse.csc_array(weights)
    if W.ndim != 2:
        raise ValueError("weights must be 2-D (sources × candidates)")
    if W.nnz and not (np.all(np.isfinite(W.data)) and W.data.min() >= 0 and W.data.max() <= 1):
        raise ValueError("weights must lie in [0, 1]")
    if not W.has_canonical_format:
        W = W.copy()  # never sort or merge the caller's matrix in place
        W.sum_duplicates()
    return W


def _check_supply(supply, n: int) -> np.ndarray:
    s = np.asarray(supply, float)
    if s.shape != (n,):
        raise ValueError(f"supply must have shape ({n},), one value per source")
    if not np.all(np.isfinite(s)) or np.any(s < 0):
        raise ValueError("supply must be finite and >= 0")
    return s


def _check_fixed(fixed: Iterable[int], m: int) -> list[int]:
    out = [int(j) for j in fixed]
    if len(set(out)) != len(out) or any(not 0 <= j < m for j in out):
        raise ValueError("fixed must hold distinct candidate positions within range")
    return out


def _open(W: sparse.csc_array, j: int, best: np.ndarray, owner: np.ndarray) -> None:
    """Open hub ``j``: sources it serves with a strictly higher weight move to it."""
    lo, hi = W.indptr[j], W.indptr[j + 1]
    idx = W.indices[lo:hi]
    w = W.data[lo:hi]
    up = w > best[idx]
    best[idx[up]] = w[up]
    owner[idx[up]] = j


def _allocate(W: sparse.csc_array, hubs: Sequence[int]) -> tuple[np.ndarray, np.ndarray]:
    """Each source to its best hub among ``hubs`` (ties to the earlier one): (owner, weight)."""
    best = np.zeros(W.shape[0])
    owner = np.full(W.shape[0], -1, np.int64)
    for j in hubs:
        _open(W, j, best, owner)
    return owner, best


def greedy_coverage(
    weights,
    supply: np.ndarray,
    *,
    q_min: float,
    max_hubs: int | None = None,
    target_share: float | None = None,
    fixed: Sequence[int] = (),
    prune: bool = True,
) -> Coverage:
    """Open hubs greedily while the best one adds at least ``q_min`` (module docstring).

    Args:
        weights: (sources × candidates) decay weights in [0, 1], sparse or dense
            (:func:`weight_matrix`).
        supply: per source, in the unit of ``q_min`` (e.g. Nm³ CH₄/d).
        q_min: minimum supply a new hub must add (same unit). A hub that adds nothing never opens.
        max_hubs: at most this many hubs besides ``fixed`` (``None``: no limit).
        target_share: stop once this share of the supply is covered (``None``: no target).
        fixed: candidate positions opened first, in this order, whatever they add (existing
            plants). They are never pruned.
        prune: close hubs left below ``q_min`` after allocation (see the module docstring).

    Returns:
        :class:`Coverage`.
    """
    W = _as_csc(weights)
    n, m = W.shape
    s = _check_supply(supply, n)
    if not (math.isfinite(q_min) and q_min >= 0):
        raise ValueError("q_min must be finite and >= 0")
    if max_hubs is not None and max_hubs < 0:
        raise ValueError("max_hubs must be >= 0")
    if target_share is not None and not 0 < target_share <= 1:
        raise ValueError("target_share must lie in (0, 1]")
    fixed_l = _check_fixed(fixed, m)
    fixed_set = set(fixed_l)

    best = np.zeros(n)
    owner = np.full(n, -1, np.int64)
    total = float(s.sum())

    def gain(j: int) -> float:
        lo, hi = W.indptr[j], W.indptr[j + 1]
        idx = W.indices[lo:hi]
        return float(np.dot(np.maximum(W.data[lo:hi] - best[idx], 0.0), s[idx]))

    rows: list[dict] = []
    covered = 0.0

    def record(j: int, g: float, is_fixed: bool) -> None:
        nonlocal covered
        _open(W, j, best, owner)
        covered += g
        rows.append(
            {"step": len(rows) + 1, "hub": j, "fixed": is_fixed, "gain": g, "covered": covered}
        )

    for j in fixed_l:
        record(j, gain(j), True)

    def reached() -> bool:
        return target_share is not None and total > 0 and covered >= target_share * total

    # Lazy greedy: heap of (-gain, candidate, number of hubs open when the gain was computed).
    # A popped gain computed with the current hubs is exact and, gains only shrinking, the best.
    heap = [(-gain(j), j, len(rows)) for j in range(m) if j not in fixed_set]
    heapq.heapify(heap)
    n_new = 0
    stop = "max_hubs" if max_hubs == 0 else "target_share" if reached() else ""
    while not stop:
        if not heap:
            stop = "exhausted"
            break
        neg, j, version = heapq.heappop(heap)
        if version != len(rows):
            heapq.heappush(heap, (-gain(j), j, len(rows)))
            continue
        g = -neg
        if g <= 0 or g < q_min:
            stop = "q_min"
            break
        record(j, g, False)
        n_new += 1
        if max_hubs is not None and n_new >= max_hubs:
            stop = "max_hubs"
        elif reached():
            stop = "target_share"

    order = [r["hub"] for r in rows]
    closed: set[int] = set()
    own, wt = owner, best
    if prune:
        step_of = {r["hub"]: r["step"] for r in rows}
        while True:
            own, wt = _allocate(W, [j for j in order if j not in closed])
            has = own >= 0
            alloc = np.bincount(own[has], weights=(s * wt)[has], minlength=m)
            below = [
                j for j in order if j not in closed and j not in fixed_set and alloc[j] < q_min
            ]
            if not below:
                break
            closed.add(min(below, key=lambda j: (alloc[j], -step_of[j])))

    has = own >= 0
    alloc = np.bincount(own[has], weights=(s * wt)[has], minlength=m)
    n_src = np.bincount(own[has & (s * wt > 0)], minlength=m)
    trace = pd.DataFrame(rows, columns=["step", "hub", "fixed", "gain", "covered"])
    trace["covered_share"] = trace["covered"] / total if total > 0 else math.nan
    hubs = pd.DataFrame(
        {
            "hub": trace["hub"].to_numpy(),
            "step": trace["step"].to_numpy(),
            "fixed": trace["fixed"].to_numpy(bool),
            "gain_at_entry": trace["gain"].to_numpy(float),
            "closed": np.array([j in closed for j in order], bool),
            "supply_allocated": alloc[order] if order else np.zeros(0),
            "n_sources": n_src[order] if order else np.zeros(0, np.int64),
        }
    )
    hubs["meets_qmin"] = ~hubs["closed"] & (hubs["supply_allocated"] >= q_min)
    return Coverage(
        trace=trace,
        hubs=hubs,
        owner=own,
        weight=wt,
        total_supply=total,
        covered=float(alloc.sum()),
        covered_greedy=covered,
        q_min=float(q_min),
        stop_reason=stop,
    )


def hubs_for_share(trace: pd.DataFrame, shares: Sequence[float] = (0.5, 0.8)) -> pd.DataFrame:
    """Hubs needed, in opening order, to cover each share of the supply (the coverage curve).

    ``n_hubs`` counts fixed hubs too, ``n_new`` only the greedy ones; ``<NA>`` when the run
    never reaches the share. Read from the greedy trace, before pruning.
    """
    cs = trace["covered_share"].to_numpy(float)
    fx = trace["fixed"].to_numpy(bool)
    rows = []
    for sh in shares:
        hit = np.flatnonzero(cs >= sh)
        k = int(hit[0]) + 1 if len(hit) else None
        rows.append(
            {
                "share": float(sh),
                "n_hubs": k if k is not None else pd.NA,
                "n_new": int(k - fx[:k].sum()) if k is not None else pd.NA,
            }
        )
    return pd.DataFrame(rows).astype({"n_hubs": "Int64", "n_new": "Int64"})


@dataclass(frozen=True)
class UpperBound:
    """All candidates whose own catchment reaches ``q_min`` open at once (ESD variant A)."""

    n_viable: int
    covered: float
    covered_share: float


def coverage_upper_bound(
    weights, supply: np.ndarray, *, q_min: float, fixed: Sequence[int] = ()
) -> UpperBound:
    """Supply covered when every viable candidate opens, each source counted once.

    A candidate is viable when its own weighted catchment, sum_i s_i w_ij, is > 0 and reaches
    ``q_min``, overlaps with other catchments ignored. Every hub the greedy opens is viable, so
    this bounds :func:`greedy_coverage` from above (same ``fixed``).
    """
    W = _as_csc(weights)
    n, m = W.shape
    s = _check_supply(supply, n)
    fixed_l = _check_fixed(fixed, m)
    col = np.repeat(np.arange(m), np.diff(W.indptr))
    catchment = np.bincount(col, weights=W.data * s[W.indices], minlength=m)
    viable = (catchment > 0) & (catchment >= q_min)
    viable[fixed_l] = False
    _, wt = _allocate(W, [*fixed_l, *np.flatnonzero(viable).tolist()])
    total = float(s.sum())
    covered = float(np.dot(s, wt))
    return UpperBound(
        n_viable=int(viable.sum()),
        covered=covered,
        covered_share=covered / total if total > 0 else math.nan,
    )


def hub_breakdown(
    cov: Coverage, parts: Mapping[str, np.ndarray], cell_id: np.ndarray | None = None
) -> pd.DataFrame:
    """Supply each open hub collects, split into parts, with the number of cells behind each part.

    Args:
        cov: :func:`greedy_coverage` result.
        parts: per-source amounts (e.g. farm-register vs other residues), same unit as the
            supply; they need not add up to it.
        cell_id: per source, the cell it sits in (default: its position), so that two sources
            in one cell (two material classes) count as one cell.

    Returns:
        One row per open hub: ``hub``, and per part ``<part>`` (sum of amount × weight) and
        ``<part>_cells`` (distinct cells with amount > 0 allocated to the hub). Use the counts for
        minimum-count disclosure rules (k >= 3 farm cells, docs/inbox/esd_n3_grid.md §4).
    """
    own, wt = cov.owner, cov.weight
    cid = np.arange(len(own)) if cell_id is None else np.asarray(cell_id)
    if cid.shape != own.shape:
        raise ValueError("cell_id must have one value per source")
    out = pd.DataFrame({"hub": cov.hubs.loc[~cov.hubs["closed"], "hub"].to_numpy()})
    has = own >= 0
    for name, v in parts.items():
        v = np.asarray(v, float)
        if v.shape != own.shape:
            raise ValueError(f"part {name!r} must have one value per source")
        amount = pd.Series(v[has] * wt[has]).groupby(own[has]).sum()
        pos = has & (v > 0)
        cells = pd.DataFrame({"hub": own[pos], "cell": cid[pos]}).drop_duplicates()
        n_cells = cells.groupby("hub").size()
        out[name] = out["hub"].map(amount).fillna(0.0).astype(float)
        out[f"{name}_cells"] = out["hub"].map(n_cells).fillna(0).astype(int)
    return out


def source_rows(
    x: np.ndarray,
    y: np.ndarray,
    table: pd.DataFrame,
    residue_class: Mapping[str, str],
    *,
    farm: Iterable[str] = (),
    route: Mapping[str, str] | None = None,
    cell_m: float | None = None,
) -> pd.DataFrame:
    """Supply rows for :func:`weight_matrix`: one per position, material class and route.

    Args:
        x, y: positions (m, one projected CRS), one per row of ``table``.
        table: supply per residue (columns), e.g. Nm³ CH₄/d; NaN counts as 0.
        residue_class: material class of each residue (e.g. ``liquid``); every column of
            ``table`` needs one.
        farm: residues taken from farm registers, kept apart in ``farm`` for disclosure rules.
        route: residue -> label for residues restricted to some candidates (e.g. straw to
            mills); the others get the label ``""``.
        cell_m: if set, positions are snapped to squares of this side (m) and summed.

    Returns:
        Columns ``cell`` (position id), ``x``, ``y`` (square centre when snapped), ``cls``,
        ``route``, ``supply`` = ``farm`` + ``nonfarm``; rows with no supply are dropped.
    """
    route = dict(route or {})
    farm = set(farm)
    missing = [c for c in table.columns if c not in residue_class]
    if missing:
        raise ValueError(f"no material class for residues {missing}")
    x = np.asarray(x, float)
    y = np.asarray(y, float)
    if not len(x) == len(y) == len(table):
        raise ValueError("x, y and table must have one entry per row")
    if cell_m:
        ix, iy = np.floor(x / cell_m), np.floor(y / cell_m)
        pos = pd.DataFrame({"x": (ix + 0.5) * cell_m, "y": (iy + 0.5) * cell_m})
    else:
        pos = pd.DataFrame({"x": x, "y": y})
    cell = pos.groupby(["x", "y"], sort=False).ngroup().to_numpy()
    v = table.fillna(0.0).to_numpy(float)
    if np.any(v < 0):
        raise ValueError("supply must be >= 0")
    parts = []
    keys = sorted({(residue_class[c], route.get(c, "")) for c in table.columns})
    for cls, rt in keys:
        cols = [
            k
            for k, c in enumerate(table.columns)
            if (residue_class[c], route.get(c, "")) == (cls, rt)
        ]
        is_farm = [k for k in cols if table.columns[k] in farm]
        not_farm = [k for k in cols if table.columns[k] not in farm]
        parts.append(
            pd.DataFrame(
                {
                    "cell": cell,
                    "cls": cls,
                    "route": rt,
                    "farm": v[:, is_farm].sum(axis=1),
                    "nonfarm": v[:, not_farm].sum(axis=1),
                }
            )
        )
    long = pd.concat(parts, ignore_index=True)
    out = long.groupby(["cell", "cls", "route"], as_index=False, sort=True)[
        ["farm", "nonfarm"]
    ].sum()
    out["supply"] = out["farm"] + out["nonfarm"]
    out = out[out["supply"] > 0].reset_index(drop=True)
    first = pos.groupby(cell).first()
    out["x"] = out["cell"].map(first["x"])
    out["y"] = out["cell"].map(first["y"])
    return out[["cell", "x", "y", "cls", "route", "supply", "farm", "nonfarm"]]


def withhold_small_counts(table: pd.DataFrame, part: str, k_min: int) -> pd.DataFrame:
    """Minimum-count disclosure rule on one part of a :func:`hub_breakdown` table.

    ``<part>`` becomes NaN, and ``<part>_withheld`` True, where ``0 < <part>_cells < k_min``.
    Before publishing a total over all hubs, check with :func:`cells_behind` that the withheld
    hubs hold no cells or at least ``k_min`` together: the total minus the published rows gives
    their sum.
    """
    out = table.copy()
    n = out[f"{part}_cells"]
    held = (n > 0) & (n < k_min)
    out[part] = out[part].where(~held)
    out[f"{part}_withheld"] = held
    return out


def cells_behind(
    cov: Coverage, values: np.ndarray, hubs: Iterable[int], cell_id: np.ndarray | None = None
) -> int:
    """Distinct cells with ``values > 0`` whose sources are allocated to any of ``hubs``."""
    own = cov.owner
    v = np.asarray(values, float)
    cid = np.arange(len(own)) if cell_id is None else np.asarray(cell_id)
    if v.shape != own.shape or cid.shape != own.shape:
        raise ValueError("values and cell_id must have one entry per source")
    sel = np.isin(own, np.fromiter(hubs, np.int64)) & (v > 0)
    return int(len(np.unique(cid[sel])))
