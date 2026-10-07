"""Score the suitability grid v0: equal weights, Dirichlet rank stability, one-at-a-time check.

ADR-0016, docs/12 Step 2. Reads ``suitability_grid_v0.parquet`` (built on the PC from the
PILAR-2b export + EPE layers, cells at H3 res 7) and writes, next to it:

- ``suitability_score_v0.parquet``: per cell, normalised criteria, equal-weight score/rank and
  rank stability (median, 5-95 % rank, share of draws in the top k);
- ``suitability_bounds_v0.csv``, ``suitability_oat_v0.csv``, ``suitability_draws_v0.csv``;
- ``suitability_top_cells_v0.csv`` and ``suitability_municipal_v0.csv`` (best cell per
  municipality);
- ``suitability_sites_spaced_v0.csv``: distinct candidate sites, at least ``--spacing-km``
  apart, picked by equal-weight rank and, separately, by robustness (share of weight draws in
  the top k), because neighbouring cells share most of their 30 km sums;
- ``suitability_map_v0.csv``: the input of ``webgis/aptidao_biometano_sp.html``;
- ``suitability_score_v0_meta.json``: run_id, parameter hash, input sha256.

Run:  uv run python scripts/siting/score_grid_v0.py <folder holding suitability_grid_v0.parquet>
          [--exclude federal_uc_integral=<FEDERAL_PROTECTED_AREAS_INTEGRAL_PROTECTION_v2.shp>]

``--exclude label=path`` (repeatable) adds a hard exclusion: cells whose centre lies in a polygon
of the layer (``engine.siting.exclusions``; needs shapely, pyproj, pyogrio). Use only layers
with a legal basis and a ``sources.yaml`` entry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import h3
import pandas as pd

from engine.siting.suitability import (
    Criterion,
    equal_weights,
    normalize,
    one_at_a_time,
    spaced_selection,
    weight_sensitivity,
)

# name, input column, direction. Distances are straight-line (geodesic) km: screening only.
# Feedstock is 4 of 8 criteria, so equal weights already lean on supply; the map lets you change it.
SPEC = [
    ("gas", "gas_network_km", "lower_better"),  # min of delivery point, transport, distribution
    ("power", "substation_km", "lower_better"),
    ("road", "highway_km", "lower_better"),
    ("cane", "cane_t_30km", "higher_better"),
    ("swine", "swine_head_30km", "higher_better"),
    ("poultry", "poultry_head_30km", "higher_better"),
    ("cattle", "cattle_head_30km", "higher_better"),
    ("demand", "population_30km", "higher_better"),
]
GAS_COLS = ["gas_delivery_point_km", "gas_pipeline_transport_km", "gas_pipeline_distribution_km"]
# Upper bound = 99th percentile of non-excluded cells, so outliers don't flatten the scale.
P_HI = 0.99
N_DRAWS, TOP_K, SEED = 1000, 100, 20261007
PER_ROW = ["score_base", "rank_base", "rank_median", "rank_p05", "rank_p95", "p_top_k"]
NOTE = f"0 to p{int(P_HI * 100)} of non-excluded cells"


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main(folder: Path, exclude: dict[str, Path], spacing_km: float, n_sites: int) -> None:
    src = folder / "suitability_grid_v0.parquet"
    g = pd.read_parquet(src).set_index("h3_index")
    g["gas_network_km"] = g[GAS_COLS].min(axis=1)
    lat, lon = zip(*(h3.cell_to_latlng(c) for c in g.index), strict=True)
    g["excluded"] = g["excluded"].astype(bool)
    extra = {}
    for label, path in exclude.items():
        from engine.siting.exclusions import points_in_layer

        hit = points_in_layer(lat, lon, path)
        g[f"excl_{label}"] = hit
        extra[label] = {
            "file": Path(path).name,
            "sha256": sha256(Path(path)),
            "cells_inside": int(hit.sum()),
            "newly_excluded": int((hit & ~g["excluded"]).sum()),
        }
        g["excluded"] |= hit
    keep = ~g["excluded"]

    crit = []
    for name, col, d in SPEC:
        hi = float(g.loc[keep, col].quantile(P_HI))
        crit.append(Criterion(name, col, d, lo=0.0, hi=hi, note=NOTE))
    norm, bounds = normalize(g, crit)
    w = equal_weights(crit)

    per_row, draws = weight_sensitivity(
        norm,
        base_weights=w,
        n=N_DRAWS,
        concentration=1.0,
        top_k=TOP_K,
        seed=SEED,
        excluded=g["excluded"],
    )
    oat = one_at_a_time(norm, w, delta=0.2, top_k=TOP_K, excluded=g["excluded"])

    out = pd.concat([g[["ibge_code", "excluded"]], norm.add_prefix("n_"), per_row], axis=1)
    out.to_parquet(folder / "suitability_score_v0.parquet")
    bounds.to_csv(folder / "suitability_bounds_v0.csv", index=False)
    oat.to_csv(folder / "suitability_oat_v0.csv", index=False)
    draws.to_csv(folder / "suitability_draws_v0.csv", index=False)

    raw_cols = [c for _, c, _ in SPEC]
    top = out.dropna(subset=["rank_base"]).sort_values("rank_base").head(200)
    top.join(g[raw_cols]).to_csv(folder / "suitability_top_cells_v0.csv")

    ok = out.dropna(subset=["score_base"])
    best = ok.loc[ok.groupby("ibge_code")["score_base"].idxmax()]
    mun = best[["ibge_code", "score_base", "rank_base", "p_top_k"]].rename(
        columns={
            "score_base": "best_cell_score",
            "rank_base": "best_cell_rank",
            "p_top_k": "best_cell_p_top_k",
        }
    )
    mun["best_cell_h3"] = best.index
    in_top = ok[ok["rank_base"] <= 1000].groupby("ibge_code").size()
    mun["cells_in_top_1000"] = mun["ibge_code"].map(in_top).fillna(0).astype(int)
    mun.sort_values("best_cell_rank").to_csv(folder / "suitability_municipal_v0.csv", index=False)

    # Distinct sites: best cells at least spacing_km apart, by score and by robustness.
    pos = pd.Series(range(len(out)), index=out.index)
    sites = []
    orders = {
        "equal_weights": ok.sort_values("rank_base").index,
        "robust": ok.sort_values(["p_top_k", "rank_base"], ascending=[False, True]).index,
    }
    for name, idx in orders.items():
        pick = spaced_selection(lat, lon, pos[idx].to_numpy(), min_km=spacing_km, n=n_sites)
        sel = out.iloc[pick][["ibge_code", *PER_ROW]]
        sel = sel.join(g[raw_cols]).assign(list=name, site=range(1, len(pick) + 1))
        sel["lat"], sel["lon"] = [lat[i] for i in pick], [lon[i] for i in pick]
        sites.append(sel)
    sites = pd.concat(sites)
    sites.to_csv(folder / "suitability_sites_spaced_v0.csv")

    # Map input: n_* in [0, 1] + raw values for the tooltip, rounded to keep the file small.
    m = pd.DataFrame(
        {
            "h3_index": g.index,
            "ibge_code": g["ibge_code"].to_numpy(),
            "lat": lat,
            "lon": lon,
            "excluded": g["excluded"].astype(int).to_numpy(),
        }
    )
    for c in norm.columns:
        m[f"n_{c}"] = norm[c].round(3).to_numpy()
    for c in raw_cols:
        m[c] = g[c].round(1).to_numpy()
    m.round({"lat": 5, "lon": 5}).to_csv(folder / "suitability_map_v0.csv", index=False)

    params = {
        "criteria": bounds.to_dict("records"),
        "weights": w,
        "n_draws": N_DRAWS,
        "top_k": TOP_K,
        "seed": SEED,
        "concentration": 1.0,
        "oat_delta": 0.2,
        "spacing_km": spacing_km,
        "n_sites": n_sites,
        "extra_exclusions": {k: v["sha256"] for k, v in extra.items()},
    }
    phash = hashlib.sha256(json.dumps(params, sort_keys=True, default=str).encode()).hexdigest()
    meta = {
        "run_id": "suitability_v0_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
        "param_hash": phash,
        "input": {"file": src.name, "sha256": sha256(src)},
        "cells": int(len(g)),
        "excluded": int((~keep).sum()),
        "extra_exclusions": extra,
        "scored": int(out["score_base"].notna().sum()),
        "robust_top_k_cells_p50": int((per_row["p_top_k"] >= 0.5).sum()),
        "oat_min_top_k_kept": float(oat["top_k_kept"].min()),
        "params": params,
        "caveats": [
            "straight-line distances, not road network",
            "gas layer is a trunk summary (docs/21 Q17)",
            "municipal cane and herds spread uniformly by area (flag D)",
            "exclusions: state protected areas and indigenous territories"
            + "".join(f", {k}" for k in extra)
            + " (cell centre inside)",
        ],
    }
    (folder / "suitability_score_v0_meta.json").write_text(json.dumps(meta, indent=2, default=str))
    print(json.dumps({k: v for k, v in meta.items() if k != "params"}, indent=2))
    print(oat.to_string(index=False))
    cols = ["ibge_code", "score_base", "rank_median", "rank_p05", "rank_p95", "p_top_k"]
    print(top.head(15)[cols].to_string())
    print(f"\nDistinct sites >= {spacing_km:g} km apart:")
    for name in orders:
        sub = sites[sites["list"] == name].head(15)
        print(f"-- {name}\n" + sub[["site", *cols]].to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("folder", type=Path)
    ap.add_argument("--exclude", action="append", default=[], metavar="LABEL=PATH")
    ap.add_argument("--spacing-km", type=float, default=30.0)
    ap.add_argument("--n-sites", type=int, default=30)
    a = ap.parse_args()
    excl = dict(e.split("=", 1) for e in a.exclude)
    main(a.folder, {k: Path(v) for k, v in excl.items()}, a.spacing_km, a.n_sites)
