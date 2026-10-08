"""engine.siting.coverage: greedy hub coverage with a minimum scale, on synthetic data."""

import itertools

import numpy as np
import pandas as pd
import pytest
from scipy import sparse

from engine.siting.coverage import (
    cells_behind,
    coverage_upper_bound,
    decay_weight,
    fallback_pairs_km,
    fallback_weight_matrix,
    greedy_coverage,
    hub_breakdown,
    hubs_for_share,
    pairs_from_dense,
    source_rows,
    sphere_xyz_m,
    weight_matrix,
    withhold_small_counts,
)
from engine.siting.routing import fallback_road_km


def random_case(seed: int, n: int = 60, m: int = 25, r1: float = 3.0, r2: float = 8.0):
    """Sources and candidates on a 20 km square, decay weights, lognormal supply."""
    rng = np.random.default_rng(seed)
    src = rng.random((n, 2)) * 20_000
    cand = rng.random((m, 2)) * 20_000
    i, j, d = fallback_pairs_km(src, cand, max_road_km=r2, detour_factor=1.0)
    W = weight_matrix(i, j, d, r1, r2, (n, m))
    s = rng.lognormal(0.0, 1.0, n)
    return W, s


def naive_greedy(W, s, q_min):
    """Reference: recompute every gain at every step (dense), lowest position on ties."""
    Wd = W.toarray()
    best = np.zeros(len(s))
    opened, gains = [], []
    while True:
        g = np.maximum(Wd - best[:, None], 0.0).T @ s
        g[opened] = -np.inf
        j = int(np.argmax(g))
        if not np.isfinite(g[j]) or g[j] <= 0 or g[j] < q_min:
            return opened, gains
        opened.append(j)
        gains.append(float(g[j]))
        best = np.maximum(best, Wd[:, j])


def test_decay_weight_values_step_and_errors():
    got = decay_weight([0, 5, 10, 12.5, 15, 20, np.nan], 10, 15)
    assert got == pytest.approx([1, 1, 1, 0.5, 0, 0, 0])
    assert decay_weight([9.9, 10, 10.1], 10, 10) == pytest.approx([1, 1, 0])  # MCLP radius
    for bad in ((1, 15, 10), (-1, 10, 15), (1, np.nan, 15)):
        with pytest.raises(ValueError):
            decay_weight(*bad)


def test_fallback_pairs_match_brute_force():
    rng = np.random.default_rng(3)
    src = rng.random((80, 2)) * 50_000
    cand = np.vstack([src[:1], rng.random((20, 2)) * 50_000])  # candidate 0 sits on source 0
    i, j, d = fallback_pairs_km(src, cand, max_road_km=20, detour_factor=1.3)
    straight = np.hypot(*(src[:, None, :] - cand[None, :, :]).transpose(2, 0, 1)) / 1000
    ri, rj = np.nonzero(straight * 1.3 <= 20)
    assert set(zip(i.tolist(), j.tolist(), strict=True)) == set(
        zip(ri.tolist(), rj.tolist(), strict=True)
    )
    assert d == pytest.approx(straight[i, j] * 1.3)
    assert (0, 0) in set(zip(i.tolist(), j.tolist(), strict=True))
    with pytest.raises(ValueError, match="detour_factor"):
        fallback_pairs_km(src, cand, max_road_km=20, detour_factor=0.9)


def test_sphere_positions_give_the_routing_fallback_distance():
    rng = np.random.default_rng(11)
    src = np.column_stack([rng.uniform(-25.0, -20.0, 40), rng.uniform(-53.0, -44.0, 40)])
    cand = np.column_stack([rng.uniform(-25.0, -20.0, 30), rng.uniform(-53.0, -44.0, 30)])
    i, j, d = fallback_pairs_km(
        sphere_xyz_m(src[:, 0], src[:, 1]),
        sphere_xyz_m(cand[:, 0], cand[:, 1]),
        max_road_km=300,
        detour_factor=1.295,
    )
    ref = fallback_road_km(src, cand, 1.295)
    ri, rj = np.nonzero(ref <= 300)
    assert len(i) > 50
    assert set(zip(i.tolist(), j.tolist(), strict=True)) == set(
        zip(ri.tolist(), rj.tolist(), strict=True)
    )
    assert d == pytest.approx(ref[i, j], rel=2e-4)  # chord vs arc at <= 300 km
    near = ref[i, j] <= 60 * 1.295
    assert d[near] == pytest.approx(ref[i, j][near], rel=4e-6)
    with pytest.raises(ValueError, match="same number of coordinates"):
        fallback_pairs_km(src, sphere_xyz_m(cand[:, 0], cand[:, 1]), max_road_km=9, detour_factor=1)


def test_pairs_from_dense_drops_unreachable_and_far():
    i, j, d = pairs_from_dense(np.array([[1.0, np.nan], [30.0, 0.0]]), max_km=25)
    assert list(zip(i.tolist(), j.tolist(), d.tolist(), strict=True)) == [(0, 0, 1.0), (1, 1, 0.0)]


def test_weight_matrix_uses_each_source_radii():
    # source 0 is a liquid (5-15 km), source 1 a dry solid (10-25 km)
    W = weight_matrix(
        [0, 1, 0, 1], [0, 0, 1, 1], [12.0, 12.0, 16.0, 0.0], [5, 10], [15, 25], (2, 2)
    )
    assert W.toarray() == pytest.approx(np.array([[0.3, 0.0], [13 / 15, 1.0]]))
    assert W.nnz == 3  # the liquid source 16 km away carries no weight
    with pytest.raises(ValueError, match="repeated"):
        weight_matrix([0, 0], [1, 1], [1.0, 2.0], 5, 15, (1, 2))
    with pytest.raises(ValueError, match="out of range"):
        weight_matrix([2], [0], [1.0], 5, 15, (2, 2))


@pytest.mark.parametrize("seed", range(6))
def test_lazy_greedy_equals_naive_greedy(seed):
    W, s = random_case(seed)
    q_min = float(np.quantile(s, 0.5))
    cov = greedy_coverage(W, s, q_min=q_min, prune=False)
    opened, gains = naive_greedy(W, s, q_min)
    assert cov.trace["hub"].tolist() == opened
    assert cov.trace["gain"].to_numpy() == pytest.approx(gains)
    assert cov.stop_reason == "q_min"


@pytest.mark.parametrize("prune", [False, True])
def test_each_source_counts_once_at_its_best_open_hub(prune):
    W, s = random_case(11, n=120, m=40)
    q_min = 2.0
    cov = greedy_coverage(W, s, q_min=q_min, prune=prune)
    Wd = W.toarray()
    open_hubs = cov.hubs.loc[~cov.hubs["closed"], "hub"].to_numpy()
    best = Wd[:, open_hubs].max(axis=1) if len(open_hubs) else np.zeros(len(s))
    assert cov.weight == pytest.approx(best)
    covered = cov.owner >= 0
    assert Wd[np.flatnonzero(covered), cov.owner[covered]] == pytest.approx(cov.weight[covered])
    assert cov.covered == pytest.approx(cov.hubs["supply_allocated"].sum())
    assert cov.covered == pytest.approx(float(s @ best))
    assert (cov.trace["gain"] >= q_min).all()
    if prune:
        assert cov.hubs.loc[~cov.hubs["closed"], "meets_qmin"].all()
    else:
        # stopped for good: no candidate left adds q_min
        rest = np.setdiff1d(np.arange(W.shape[1]), open_hubs)
        assert (np.maximum(Wd[:, rest] - cov.weight[:, None], 0.0).T @ s < q_min).all()


def test_greedy_is_a_heuristic_and_can_miss_the_best_pair():
    # binary weights (r1 = r2, the MCLP); X sits between the two clusters and catches a bit more
    s = np.array([2.0, 2.0, 2.0, 2.0, 1.0])  # a1, a2, b1, b2, m
    W = np.array(
        [
            # X  Y  Z
            [0, 1, 0],  # a1
            [1, 1, 0],  # a2
            [1, 0, 1],  # b1
            [0, 0, 1],  # b2
            [1, 0, 0],  # m
        ],
        float,
    )
    cov = greedy_coverage(W, s, q_min=0.0, max_hubs=2)
    assert cov.trace["hub"].tolist() == [0, 1] and cov.covered == pytest.approx(7.0)
    best_pair = max(s @ W[:, list(p)].max(axis=1) for p in itertools.combinations(range(3), 2))
    assert best_pair == pytest.approx(8.0)  # Y + Z


def decay_case():
    """Hub A reaches both sources at weight 0.75; B and C each sit on one source."""
    s = np.array([10.0, 10.0])
    W = np.array([[0.75, 1.0, 0.0], [0.75, 0.0, 1.0]])  # columns A, B, C
    return W, s


def test_a_hub_emptied_by_later_hubs_is_flagged_or_pruned():
    W, s = decay_case()
    kept = greedy_coverage(W, s, q_min=2.0, prune=False)
    assert kept.trace["hub"].tolist() == [0, 1, 2]  # A adds 15, then B and C 2.5 each
    a = kept.hubs.set_index("hub").loc[0]
    assert a["supply_allocated"] == 0 and not a["meets_qmin"] and not a["closed"]
    pruned = greedy_coverage(W, s, q_min=2.0)
    h = pruned.hubs.set_index("hub")
    assert h.loc[0, "closed"] and h.loc[[1, 2], "supply_allocated"].tolist() == [10.0, 10.0]
    assert pruned.covered == pytest.approx(20.0) and pruned.covered_greedy == pytest.approx(20.0)
    only_a = greedy_coverage(W, s, q_min=3.0)
    assert only_a.trace["hub"].tolist() == [0] and only_a.covered == pytest.approx(15.0)


def test_fixed_hubs_open_first_and_are_never_pruned():
    W, s = decay_case()
    cov = greedy_coverage(W, s, q_min=2.0, fixed=[1])
    assert cov.trace["hub"].tolist() == [1, 2] and cov.trace["fixed"].tolist() == [True, False]
    big = greedy_coverage(W, s, q_min=100.0, fixed=[0])
    row = big.hubs.iloc[0]
    assert row["fixed"] and not row["closed"] and not row["meets_qmin"]
    assert big.covered == pytest.approx(15.0)


def clusters():
    """Four separate clusters, supply 4, 3, 2 and 1, one candidate each (binary weights)."""
    return np.eye(4), np.array([4.0, 3.0, 2.0, 1.0])


def test_stop_rules_and_coverage_curve():
    W, s = clusters()
    full = greedy_coverage(W, s, q_min=0.0)
    assert full.stop_reason == "exhausted" and full.trace["covered_share"].tolist() == [
        pytest.approx(x) for x in (0.4, 0.7, 0.9, 1.0)
    ]
    curve = hubs_for_share(full.trace, (0.5, 0.9, 1.0))
    assert curve["n_hubs"].tolist() == [2, 3, 4] and curve["n_new"].tolist() == [2, 3, 4]
    two = greedy_coverage(W, s, q_min=0.0, max_hubs=2)
    assert two.stop_reason == "max_hubs" and two.covered == pytest.approx(7.0)
    assert hubs_for_share(two.trace, (0.9,))["n_hubs"].isna().all()
    target = greedy_coverage(W, s, q_min=0.0, target_share=0.7)
    assert target.stop_reason == "target_share" and len(target.trace) == 2
    scale = greedy_coverage(W, s, q_min=2.0)
    assert scale.stop_reason == "q_min" and scale.trace["hub"].tolist() == [0, 1, 2]
    none = greedy_coverage(W, s, q_min=0.0, max_hubs=0)
    assert none.trace.empty and none.covered == 0 and (none.owner == -1).all()
    fixed = greedy_coverage(W, s, q_min=0.0, fixed=[3])
    # the fixed hub covers 0.1, the first greedy hub brings it to 0.5
    assert hubs_for_share(fixed.trace, (0.5,)).iloc[0][["n_hubs", "n_new"]].tolist() == [2, 1]


@pytest.mark.parametrize("seed", range(4))
def test_upper_bound_bounds_the_greedy(seed):
    W, s = random_case(seed)
    q_min = float(np.quantile(s, 0.5))
    cov = greedy_coverage(W, s, q_min=q_min, prune=False)
    ub = coverage_upper_bound(W, s, q_min=q_min)
    assert ub.covered >= cov.covered_greedy - 1e-9
    assert ub.n_viable >= len(cov.trace)
    Wc, sc = clusters()
    assert coverage_upper_bound(Wc, sc, q_min=2.0).covered == pytest.approx(9.0)


def test_hub_breakdown_counts_a_cell_once():
    # sources 0 and 1 are two material classes in one cell; source 2 is another cell
    W = np.array([[1.0], [0.5], [1.0]])
    s = np.array([4.0, 2.0, 1.0])
    cov = greedy_coverage(W, s, q_min=1.0)
    farm = np.array([3.0, 2.0, 0.0])
    other = s - farm
    out = hub_breakdown(cov, {"farm": farm, "other": other}, cell_id=np.array([7, 7, 8]))
    row = out.iloc[0]
    assert row["farm"] == pytest.approx(3.0 + 1.0) and row["farm_cells"] == 1
    assert row["other"] == pytest.approx(1.0 + 0.0 + 1.0) and row["other_cells"] == 2


def test_inputs_are_checked_and_the_callers_matrix_is_left_alone():
    W, s = clusters()
    for kw in (
        {"supply": -s},
        {"supply": s[:3]},
        {"q_min": -1.0},
        {"q_min": np.nan},
        {"fixed": [1, 1]},
        {"fixed": [9]},
        {"target_share": 0.0},
        {"max_hubs": -1},
    ):
        args = {"supply": s, "q_min": 0.0, **kw}
        with pytest.raises(ValueError):
            greedy_coverage(W, args.pop("supply"), **args)
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        greedy_coverage(W * 2, s, q_min=0.0)
    # a column with unsorted row indices: not canonical, must not be reordered in place
    M = sparse.csc_array((np.array([0.5, 1.0]), np.array([1, 0]), np.array([0, 2])), shape=(2, 1))
    assert not M.has_canonical_format
    cov = greedy_coverage(M, np.array([1.0, 1.0]), q_min=0.0)
    assert M.indices.tolist() == [1, 0] and cov.covered == pytest.approx(1.5)
    assert isinstance(cov.hubs, pd.DataFrame)


def test_chunked_fallback_weights_equal_one_block_and_respect_routes():
    rng = np.random.default_rng(5)
    src = rng.random((300, 2)) * 60_000
    cand = rng.random((70, 2)) * 60_000
    r1 = np.where(np.arange(300) % 2, 5.0, 10.0)
    r2 = np.where(np.arange(300) % 2, 15.0, 25.0)
    i, j, d = fallback_pairs_km(src, cand, max_road_km=25, detour_factor=1.3)
    one = weight_matrix(i, j, d, r1, r2, (300, 70)).toarray()
    chunked = fallback_weight_matrix(src, cand, r1, r2, detour_factor=1.3, chunk=16)
    assert chunked.shape == (300, 70) and chunked.has_canonical_format
    assert chunked.toarray() == pytest.approx(one)
    # sources 0-99 may only go to candidates 0-9 (e.g. straw to mills)
    routed = fallback_weight_matrix(
        src, cand, r1, r2, detour_factor=1.3, chunk=16, keep_pair=lambda i, j: (i >= 100) | (j < 10)
    ).toarray()
    assert not routed[:100, 10:].any()
    assert routed[:100, :10] == pytest.approx(one[:100, :10])
    assert routed[100:] == pytest.approx(one[100:])


def test_source_rows_split_classes_routes_and_farm_parts():
    table = pd.DataFrame(
        {
            "VINHACA": [5.0, 0.0, 0.0],
            "SUINOS": [1.0, 2.0, 0.0],
            "PALHA": [3.0, 0.0, 0.0],
            "BAGACO": [0.0, 0.0, 4.0],
        }
    )
    classes = {"VINHACA": "liquid", "SUINOS": "liquid", "PALHA": "dry", "BAGACO": "dry"}
    # rows 0 and 1 fall in one 2 km square, row 2 in another
    x, y = np.array([500.0, 1500.0, 4500.0]), np.array([500.0, 500.0, 500.0])
    rows = source_rows(x, y, table, classes, farm=["SUINOS"], route={"PALHA": "mills"}, cell_m=2000)
    got = {(r.cell, r.cls, r.route): (r.supply, r.farm, r.nonfarm) for r in rows.itertuples()}
    assert got == {
        (0, "dry", "mills"): (3.0, 0.0, 3.0),
        (0, "liquid", ""): (8.0, 3.0, 5.0),
        (1, "dry", ""): (4.0, 0.0, 4.0),
    }
    assert rows.loc[rows["cell"] == 0, "x"].unique().tolist() == [1000.0]
    plain = source_rows(x, y, table, classes)
    assert len(plain["cell"].unique()) == 3 and plain["supply"].sum() == pytest.approx(15.0)
    with pytest.raises(ValueError, match="no material class"):
        source_rows(x, y, table, {"VINHACA": "liquid"})


def test_withhold_small_counts_and_cells_behind():
    W = np.array([[1.0, 0.0], [1.0, 0.0], [0.0, 1.0], [0.0, 1.0], [0.0, 1.0]])
    s = np.array([5.0, 5.0, 4.0, 4.0, 4.0])
    farm = np.array([1.0, 0.0, 1.0, 1.0, 1.0])
    cov = greedy_coverage(W, s, q_min=1.0)
    table = hub_breakdown(cov, {"farm": farm})
    out = withhold_small_counts(table, "farm", 3).set_index("hub")
    assert out.loc[0, "farm_withheld"] and np.isnan(out.loc[0, "farm"])
    assert not out.loc[1, "farm_withheld"] and out.loc[1, "farm"] == pytest.approx(3.0)
    held = out.index[out["farm_withheld"]]
    assert cells_behind(cov, farm, held) == 1  # below 3: no total over all hubs
    assert cells_behind(cov, farm, [0, 1], cell_id=np.array([0, 0, 1, 1, 2])) == 3
