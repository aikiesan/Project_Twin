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

``--normalization percentile`` ranks each criterion among non-excluded cells instead of the
linear 0..p99 scale (ADR-0017); outputs then carry ``_per`` (e.g. ``suitability_map_v0_per.csv``)
so the linear run is kept for comparison.

``--names <csv|shp>`` adds a ``municipio`` column (IBGE code -> name, e.g. from
``municipal_panel_v0.csv``) to the tables, the printout and the map CSV.

``--ch4 <n3_ch4_30km_med.parquet>`` (from ``n3_ch4_30km.py``) replaces the four feedstock
criteria with one, N3 CH₄ within 30 km (ADR-0017); outputs then carry ``_ch4``.

``--exclude label=path`` (repeatable) adds a hard exclusion: cells whose centre lies in a polygon
of the layer (``engine.siting.exclusions``; needs shapely, pyproj, pyogrio). Use only layers
with a legal basis and a ``sources.yaml`` entry.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

import h3
import pandas as pd

from engine.ingest.municipalities import name_map
from engine.siting.suitability import (
    NORMALIZATIONS,
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
# ADR-0017: with --ch4 these four are replaced by one criterion, N3 CH4 within 30 km.
FEEDSTOCK = ("cane", "swine", "poultry", "cattle")
CH4_COL = "ch4_n3_nm3_d_30km"
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


def main(
    folder: Path,
    exclude: dict[str, Path],
    spacing_km: float,
    n_sites: int,
    normalization: str = "linear",
    names: Path | None = None,
    ch4: Path | None = None,
) -> None:
    given = {f"--exclude {k}": v for k, v in exclude.items()} | {"--names": names, "--ch4": ch4}
    missing = [
        f"{k} {str(v)!r}" for k, v in given.items() if v is not None and not Path(v).is_file()
    ]
    if missing:  # an empty shell variable turns into "." or ""
        raise SystemExit("not a file (empty shell variable?): " + "; ".join(missing))
    tag = ("" if normalization == "linear" else f"_{normalization[:3]}") + ("_ch4" if ch4 else "")
    src = folder / "suitability_grid_v0.parquet"
    g = pd.read_parquet(src).set_index("h3_index")
    g["gas_network_km"] = g[GAS_COLS].min(axis=1)
    spec = SPEC
    info = []  # CH4 breakdown by residue group: shown with the sites, not scored
    if ch4 is not None:
        c = pd.read_parquet(ch4).set_index("h3_index")
        info = [k for k in c.columns if k.startswith("ch4_n3_") and k != CH4_COL]
        g = g.join(c[[CH4_COL, *info]], how="left")
        spec = [t for t in SPEC if t[0] not in FEEDSTOCK] + [("ch4", CH4_COL, "higher_better")]
    lat, lon = zip(*(h3.cell_to_latlng(c) for c in g.index), strict=True)
    g["excluded"] = g["excluded"].astype(bool)
    ids = ["ibge_code"]
    if names is not None:
        code = pd.to_numeric(g["ibge_code"], errors="coerce").astype("Int64")
        g["municipio"] = code.map(name_map(names)).fillna("")
        ids.append("municipio")
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
    for name, col, d in spec:
        hi = float(g.loc[keep, col].quantile(P_HI))
        crit.append(Criterion(name, col, d, lo=0.0, hi=hi, note=NOTE))
    norm, bounds = normalize(g, crit, method=normalization)
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

    out = pd.concat([g[[*ids, "excluded"]], norm.add_prefix("n_"), per_row], axis=1)
    out.to_parquet(folder / f"suitability_score_v0{tag}.parquet")
    bounds.to_csv(folder / f"suitability_bounds_v0{tag}.csv", index=False)
    oat.to_csv(folder / f"suitability_oat_v0{tag}.csv", index=False)
    draws.to_csv(folder / f"suitability_draws_v0{tag}.csv", index=False)

    raw_cols = [c for _, c, _ in spec] + info
    top = out.dropna(subset=["rank_base"]).sort_values("rank_base").head(200)
    top.join(g[raw_cols]).to_csv(folder / f"suitability_top_cells_v0{tag}.csv")

    ok = out.dropna(subset=["score_base"])
    best = ok.loc[ok.groupby("ibge_code")["score_base"].idxmax()]
    mun = best[[*ids, "score_base", "rank_base", "p_top_k"]].rename(
        columns={
            "score_base": "best_cell_score",
            "rank_base": "best_cell_rank",
            "p_top_k": "best_cell_p_top_k",
        }
    )
    mun["best_cell_h3"] = best.index
    in_top = ok[ok["rank_base"] <= 1000].groupby("ibge_code").size()
    mun["cells_in_top_1000"] = mun["ibge_code"].map(in_top).fillna(0).astype(int)
    mun.sort_values("best_cell_rank").to_csv(
        folder / f"suitability_municipal_v0{tag}.csv", index=False
    )

    # Distinct sites: best cells at least spacing_km apart, by score and by robustness.
    pos = pd.Series(range(len(out)), index=out.index)
    sites = []
    orders = {
        "equal_weights": ok.sort_values("rank_base").index,
        "robust": ok.sort_values(["p_top_k", "rank_base"], ascending=[False, True]).index,
    }
    for name, idx in orders.items():
        pick = spaced_selection(lat, lon, pos[idx].to_numpy(), min_km=spacing_km, n=n_sites)
        sel = out.iloc[pick][[*ids, *PER_ROW]]
        sel = sel.join(g[raw_cols]).assign(list=name, site=range(1, len(pick) + 1))
        sel["lat"], sel["lon"] = [lat[i] for i in pick], [lon[i] for i in pick]
        sites.append(sel)
    sites = pd.concat(sites)
    sites.to_csv(folder / f"suitability_sites_spaced_v0{tag}.csv")

    # Map input: n_* in [0, 1] + raw values for the tooltip, rounded to keep the file small.
    m = pd.DataFrame(
        {
            "h3_index": g.index,
            "ibge_code": g["ibge_code"].to_numpy(),
            **({"municipio": g["municipio"].to_numpy()} if names is not None else {}),
            "lat": lat,
            "lon": lon,
            "excluded": g["excluded"].astype(int).to_numpy(),
        }
    )
    for c in norm.columns:
        m[f"n_{c}"] = norm[c].round(3).to_numpy()
    for c in raw_cols:
        m[c] = g[c].round(1).to_numpy()
    m.round({"lat": 5, "lon": 5}).to_csv(folder / f"suitability_map_v0{tag}.csv", index=False)

    params = {
        "criteria": bounds.to_dict("records"),
        "weights": w,
        "n_draws": N_DRAWS,
        "top_k": TOP_K,
        "seed": SEED,
        "concentration": 1.0,
        "oat_delta": 0.2,
        "normalization": normalization,
        "spacing_km": spacing_km,
        "n_sites": n_sites,
        "ch4": None if ch4 is None else sha256(Path(ch4)),
        "extra_exclusions": {k: v["sha256"] for k, v in extra.items()},
    }
    phash = hashlib.sha256(json.dumps(params, sort_keys=True, default=str).encode()).hexdigest()
    meta = {
        "run_id": f"suitability_v0{tag}_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
        "param_hash": phash,
        "input": {"file": src.name, "sha256": sha256(src)},
        "cells": int(len(g)),
        "excluded": int((~keep).sum()),
        "extra_exclusions": extra,
        "names": (
            None if names is None else {"file": Path(names).name, "sha256": sha256(Path(names))}
        ),
        "ch4": None if ch4 is None else {"file": Path(ch4).name, "sha256": sha256(Path(ch4))},
        "scored": int(out["score_base"].notna().sum()),
        "robust_top_k_cells_p50": int((per_row["p_top_k"] >= 0.5).sum()),
        "oat_min_top_k_kept": float(oat["top_k_kept"].min()),
        "params": params,
        "caveats": [
            "straight-line distances, not road network",
            "gas layer is a trunk summary (docs/21 Q17)",
            (
                "feedstock = N3 CH4 within 30 km, CP2b v5.1 (flag D; farm part withheld where"
                " fewer than k farm cells)"
                if ch4
                else "municipal cane and herds spread uniformly by area (flag D)"
            ),
            "exclusions: state protected areas and indigenous territories"
            + "".join(f", {k}" for k in extra)
            + " (cell centre inside)",
        ],
    }
    (folder / f"suitability_score_v0{tag}_meta.json").write_text(
        json.dumps(meta, indent=2, default=str)
    )
    print(json.dumps({k: v for k, v in meta.items() if k != "params"}, indent=2))
    print(oat.to_string(index=False))
    cols = [*ids, "score_base", "rank_median", "rank_p05", "rank_p95", "p_top_k"]
    print(top.head(15)[cols].to_string())
    print(f"\nDistinct sites >= {spacing_km:g} km apart:")
    for name in orders:
        sub = sites[sites["list"] == name].head(15)
        print(f"-- {name}\n" + sub[["site", *cols]].to_string())
    if info:
        parts = [k for k in info if k != "ch4_n3_nonfarm_nm3_d_30km"]
        short = [k.removeprefix("ch4_n3_").removesuffix("_nm3_d_30km") + "_%" for k in parts]
        print("\nN3 CH4 within 30 km (Nm3/d) and shares by residue group (%):")
        for name in orders:
            sub = sites[sites["list"] == name].head(15)
            share = sub[parts].div(sub[CH4_COL], axis=0).mul(100).round(0)
            share.columns = short
            comp = pd.concat([sub[["site", *ids[1:], CH4_COL]].round(0), share], axis=1)
            print(f"-- {name}\n" + comp.to_string())


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # names with accents survive "> file" on Windows
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("folder", type=Path)
    ap.add_argument("--exclude", action="append", default=[], metavar="LABEL=PATH")
    ap.add_argument("--spacing-km", type=float, default=30.0)
    ap.add_argument("--n-sites", type=int, default=30)
    ap.add_argument("--normalization", choices=NORMALIZATIONS, default="linear")
    ap.add_argument(
        "--names",
        type=Path,
        help="IBGE code + name table (e.g. municipal_panel_v0.csv or the IBGE mesh shp)",
    )
    ap.add_argument(
        "--ch4",
        type=Path,
        help="n3_ch4_30km_<scenario>.parquet: replaces the 4 feedstock criteria (ADR-0017)",
    )
    a = ap.parse_args()
    excl = dict(e.split("=", 1) for e in a.exclude)
    main(
        a.folder,
        {k: Path(v) for k, v in excl.items()},
        a.spacing_km,
        a.n_sites,
        a.normalization,
        a.names,
        a.ch4,
    )
