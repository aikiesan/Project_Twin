"""Greedy hub coverage on the CP2b v5.1 N3 supply grid: how many hubs reach a minimum scale, where.

ADR-0018, docs/12 Step 1 (``engine.siting.coverage``). Reads ``grade_oferta_1km.gpkg`` (registry
``esd_n3_supply_grid_1km``; layers ``celulas`` and ``pontos``, columns ``<RESIDUE>__min|med|max``
in Nm³ CH₄/d of N3) and a candidate grid (a parquet with ``h3_index`` and ``excluded``, e.g.
``suitability_grid_v0.parquet`` or a ``suitability_score_v0*.parquet`` with more exclusions).
Hubs can open at the non-excluded H3 cells and at the ``pontos`` facilities (mills, sewage plants,
juice factories). Writes to ``--out``:

- ``hub_coverage_v0_<scenario><tag>_hubs.csv``: per hub, opening step, position, supply collected
  (non-farm by material class, farm part withheld below ``--k-min`` farm cells);
- ``hub_coverage_v0_<scenario><tag>_meta.json``: run_id, parameter hash, input sha256, inputs,
  hubs needed for 25-95 % of the supply, covered shares, the all-viable upper bound, caveats.

Nothing is written per supply cell. Farm-register residues (poultry, swine, dairy and feedlot
cattle) are LGPD-derived (docs/inbox/esd_n3_grid.md §4): their part of a hub's supply is withheld
when fewer than ``--k-min`` farm cells feed it, and the state total including them only when the
withheld hubs hold none or at least ``--k-min`` farm cells together. Outputs stay in ``data/``.

No defaults for the material class of each residue, the radii or ``--q-min``: no sourced values
exist (docs/21 Q20, Q23). The ESD config values are listed, flag S, in
``registry/inbox/esd_parameters.csv`` (rows ``fl_r1_*``, ``fl_r2_*``, ``fl_qmin_*``). Distances
are great-circle distance × ``--detour-factor`` (cite it; ``road_detour_factor_all`` = 1.295, flag
D, in parameters.csv), the fallback of ``engine.siting.routing``.

Run (needs shapely, pyproj, pyogrio):
    PYTHONPATH=src python scripts/siting/hub_coverage_v0.py <grade_oferta_1km.gpkg> \\
        <candidates.parquet> --classes residue_classes.csv \\
        --radius liquid=R1:R2 --radius wet=R1:R2 --radius dry=R1:R2 \\
        --q-min Q --detour-factor 1.295 [--scenario med] [--only-to PALHA=<tipo>] \\
        [--skip RESIDUE] [--source-cell-km 2] [--k-min 3] [--tag _x] [--out folder]

``residue_classes.csv`` has columns ``residue,class``, one row per residue in the gpkg (or name the
residue with ``--skip``). Run once with ``--list`` to print the residues and the facility types
(``tipo``) found in the gpkg, then write the csv.

Supply is summed into ``--source-cell-km`` squares in the gpkg CRS (projected, metres) to bound
memory; every position is then taken to latitude and longitude, and distances are great-circle
distances (``engine.siting.coverage.sphere_xyz_m``), the basis of the detour factors.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import h3
import numpy as np
import pandas as pd

from engine.siting.coverage import (
    cells_behind,
    coverage_upper_bound,
    fallback_weight_matrix,
    greedy_coverage,
    hub_breakdown,
    hubs_for_share,
    source_rows,
    sphere_xyz_m,
    withhold_small_counts,
)

FARM = ("AVES_CORTE", "AVES_POSTURA", "SUINOS", "BOV_LEITE", "BOV_CONFINADO")
FACILITY_FIELDS = ("loc", "tipo", "ref", "nome", "ibge")
SHARES = (0.25, 0.5, 0.75, 0.8, 0.9, 0.95)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_layer(path: Path, layer: str, scenario: str):
    """Centroid x, y (layer CRS, m), ``<RESIDUE>__<scenario>`` table, facility fields, CRS."""
    import pyogrio
    import shapely

    meta, _, geom, fields = pyogrio.raw.read(path, layer=layer, read_geometry=True)
    names = list(meta["fields"])
    suffix = f"__{scenario}"
    cols = {n[: -len(suffix)]: i for i, n in enumerate(names) if n.endswith(suffix)}
    if not cols:
        raise KeyError(f"{layer}: no column ending in {suffix!r}")
    tab = pd.DataFrame({r: np.asarray(fields[i], float) for r, i in cols.items()})
    extra = {k: np.asarray(fields[names.index(k)]) for k in FACILITY_FIELDS if k in names}
    c = shapely.centroid(shapely.from_wkb(geom))
    return shapely.get_x(c), shapely.get_y(c), tab, extra, meta.get("crs")


def parse_pairs(items: list[str], what: str) -> dict[str, str]:
    out = {}
    for it in items or []:
        key, sep, val = it.partition("=")
        if not sep or not key or not val:
            raise SystemExit(f"{what}: expected KEY=VALUE, got {it!r}")
        out[key.strip()] = val.strip()
    return out


def main(a: argparse.Namespace) -> None:
    from pyproj import CRS, Transformer

    xc, yc, tab_c, _, crs = read_layer(a.gpkg, "celulas", a.scenario)
    xp, yp, tab_p, fac, crs_p = read_layer(a.gpkg, "pontos", a.scenario)
    if str(crs) != str(crs_p):
        raise SystemExit(f"layers in different CRS: {crs} vs {crs_p}")
    layer_crs = CRS.from_user_input(crs)
    if not layer_crs.is_projected or layer_crs.axis_info[0].unit_name not in ("metre", "meter"):
        raise SystemExit(f"gpkg CRS must be projected in metres (cells are snapped): {crs}")
    to_deg = Transformer.from_crs(layer_crs, "EPSG:4326", always_xy=True)
    tab_p = tab_p.reindex(columns=tab_c.columns.union(tab_p.columns), fill_value=0.0)
    tab_c = tab_c.reindex(columns=tab_p.columns, fill_value=0.0)
    tipo = pd.Series(fac.get("tipo", np.full(len(xp), "")), dtype=str)
    if a.list:
        print("residues:", ", ".join(tab_c.columns))
        print("pontos tipo counts:", tipo.value_counts().to_dict())
        return

    classes = pd.read_csv(a.classes, dtype=str).apply(lambda s: s.str.strip())
    residue_class = dict(zip(classes["residue"], classes["class"], strict=True))
    skip = set(a.skip or [])
    used = [r for r in tab_c.columns if r not in skip]
    missing = [r for r in used if r not in residue_class]
    if missing:
        raise SystemExit(f"no class for residues {missing}: add them to --classes or --skip them")
    radii = {}
    for cls, val in parse_pairs(a.radius, "--radius").items():
        r1, _, r2 = val.partition(":")
        radii[cls] = (float(r1), float(r2))
    no_radius = sorted({residue_class[r] for r in used} - set(radii))
    if no_radius:
        raise SystemExit(f"no --radius for classes {no_radius}")
    only_to = {k: set(v.split(",")) for k, v in parse_pairs(a.only_to, "--only-to").items()}
    unknown = sorted(set().union(*only_to.values()) - set(tipo)) if only_to else []
    if unknown:
        raise SystemExit(f"--only-to: tipo {unknown} not in pontos ({sorted(set(tipo))})")

    t0 = time.time()
    rc = source_rows(
        xc,
        yc,
        tab_c[used],
        residue_class,
        farm=FARM,
        route={r: r for r in only_to},
        cell_m=a.source_cell_km * 1000 if a.source_cell_km else None,
    )
    rp = source_rows(xp, yp, tab_p[used], residue_class, farm=FARM, route={r: r for r in only_to})
    rp["cell"] += int(rc["cell"].max()) + 1 if len(rc) else 0
    rows = pd.concat([rc, rp], ignore_index=True)
    r1 = rows["cls"].map(lambda c: radii[c][0]).to_numpy(float)
    r2 = rows["cls"].map(lambda c: radii[c][1]).to_numpy(float)
    slon, slat = to_deg.transform(rows["x"].to_numpy(float), rows["y"].to_numpy(float))

    grid = pd.read_parquet(a.candidates, columns=["h3_index", "excluded"])
    grid = grid[~grid["excluded"].fillna(False).astype(bool)].reset_index(drop=True)
    if grid.empty:
        raise SystemExit("no candidate cell left after exclusions")
    lat, lon = map(np.array, zip(*(h3.cell_to_latlng(c) for c in grid["h3_index"]), strict=True))
    plon, plat = to_deg.transform(xp, yp)
    n_h3 = len(grid)
    fac_id = pd.Series(fac.get("loc", range(len(xp)))).astype(str)
    cand = pd.DataFrame(
        {
            "kind": ["h3"] * n_h3 + ["facility"] * len(xp),
            "id": [*grid["h3_index"].astype(str), *fac_id],
            "tipo": [""] * n_h3 + list(tipo),
            "nome": [""] * n_h3 + list(pd.Series(fac.get("nome", [""] * len(xp)), dtype=str)),
            "ibge": [""] * n_h3 + list(pd.Series(fac.get("ibge", [""] * len(xp)), dtype=str)),
            "lat": np.r_[lat, plat],
            "lon": np.r_[lon, plon],
        }
    )

    routes = sorted(only_to)
    code = rows["route"].map({r: k for k, r in enumerate(routes)}).fillna(-1).to_numpy(int)
    ok = np.zeros((max(len(routes), 1), len(cand)), bool)
    for k, r in enumerate(routes):
        ok[k] = cand["tipo"].isin(only_to[r]).to_numpy()

    def keep_pair(i: np.ndarray, j: np.ndarray) -> np.ndarray:
        c = code[i]
        return (c < 0) | ok[np.maximum(c, 0), j]

    W = fallback_weight_matrix(
        sphere_xyz_m(slat, slon),
        sphere_xyz_m(cand["lat"].to_numpy(), cand["lon"].to_numpy()),
        r1,
        r2,
        detour_factor=a.detour_factor,
        keep_pair=keep_pair if routes else None,
        chunk=a.chunk,
    )
    t1 = time.time()
    supply = rows["supply"].to_numpy(float)
    cov = greedy_coverage(W, supply, q_min=a.q_min)
    ub = coverage_upper_bound(W, supply, q_min=a.q_min)
    t2 = time.time()

    cls_names = sorted(rows["cls"].unique())
    parts = {
        "nonfarm": rows["nonfarm"].to_numpy(float),
        "farm": rows["farm"].to_numpy(float),
        **{f"nonfarm_{c}": np.where(rows["cls"] == c, rows["nonfarm"], 0.0) for c in cls_names},
    }
    cell_id = rows["cell"].to_numpy()
    hb = withhold_small_counts(hub_breakdown(cov, parts, cell_id), "farm", a.k_min)
    held = hb.loc[hb["farm_withheld"], "hub"].to_numpy()
    held_cells = cells_behind(cov, parts["farm"], held, cell_id)
    total_ok = held_cells == 0 or held_cells >= a.k_min
    hubs = cov.hubs[~cov.hubs["closed"]].merge(hb, on="hub")
    hubs = pd.concat([hubs, cand.iloc[hubs["hub"]].reset_index(drop=True)], axis=1)
    hubs["supply_nm3_ch4_d"] = (hubs["nonfarm"] + hubs["farm"]).where(~hubs["farm_withheld"])
    hubs["gain_at_entry"] = hubs["gain_at_entry"].where(~hubs["farm_withheld"])
    out_cols = [
        "step",
        "kind",
        "id",
        "tipo",
        "nome",
        "ibge",
        "lat",
        "lon",
        "fixed",
        "gain_at_entry",
        "supply_nm3_ch4_d",
        "nonfarm",
        *[f"nonfarm_{c}" for c in cls_names],
        "farm",
        "farm_cells",
        "farm_withheld",
        "nonfarm_cells",
    ]
    stem = f"hub_coverage_v0_{a.scenario}{a.tag}"
    out_dir = a.out or a.candidates.parent
    out_dir.mkdir(parents=True, exist_ok=True)
    hubs[out_cols].rename(
        columns={
            "gain_at_entry": "gain_at_entry_nm3_ch4_d",
            "nonfarm": "nonfarm_nm3_ch4_d",
            "farm": "farm_nm3_ch4_d",
            **{f"nonfarm_{c}": f"nonfarm_{c}_nm3_ch4_d" for c in cls_names},
        }
    ).round({"lat": 5, "lon": 5}).to_csv(out_dir / f"{stem}_hubs.csv", index=False)

    nonfarm_total = float(rows["nonfarm"].sum())
    curve = hubs_for_share(cov.trace, SHARES)
    params = {
        "scenario": a.scenario,
        "residues": {r: residue_class[r] for r in used},
        "skipped": sorted(skip),
        "radii_km": radii,
        "only_to": {k: sorted(v) for k, v in only_to.items()},
        "q_min_nm3_ch4_d": a.q_min,
        "distance": "great-circle km x detour_factor (fallback, not routed)",
        "detour_factor": a.detour_factor,
        "source_cell_km": a.source_cell_km,
        "k_min_farm_cells": a.k_min,
    }
    meta = {
        "run_id": f"{stem}_" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ"),
        "param_hash": hashlib.sha256(json.dumps(params, sort_keys=True).encode()).hexdigest(),
        "inputs": {
            "gpkg": {"file": a.gpkg.name, "sha256": sha256(a.gpkg), "crs": str(crs)},
            "candidates": {"file": a.candidates.name, "sha256": sha256(a.candidates)},
            "classes": {"file": a.classes.name, "sha256": sha256(a.classes)},
        },
        "params": params,
        "sources": {
            "rows": int(len(rows)),
            "rows_by_class": rows["cls"].value_counts().sort_index().to_dict(),
        },
        "candidates": {"h3": n_h3, "facilities": int(len(xp)), "pairs_with_weight": int(W.nnz)},
        "seconds": {"weights": round(t1 - t0, 1), "greedy_and_bound": round(t2 - t1, 1)},
        "stop_reason": cov.stop_reason,
        "hubs_open": int((~cov.hubs["closed"]).sum()),
        "hubs_closed_by_pruning": int(cov.hubs["closed"].sum()),
        "hubs_for_share": {
            str(r.share): (None if pd.isna(r.n_hubs) else int(r.n_hubs)) for r in curve.itertuples()
        },
        "nonfarm_covered_share": (
            round(float(hubs["nonfarm"].sum()) / nonfarm_total, 4) if nonfarm_total > 0 else None
        ),
        "covered_share": round(cov.covered_share, 4) if total_ok else "withheld (k rule)",
        "upper_bound_all_viable": {
            "n_viable": ub.n_viable,
            "covered_share": round(ub.covered_share, 4) if total_ok else "withheld (k rule)",
        },
        "hubs_farm_withheld": int(len(held)),
        "caveats": [
            "great-circle distance x detour factor (fallback), not routed road distances",
            "classes, radii and q_min are run inputs with no sourced value (docs/21 Q20, Q23)",
            "supply summed into source_cell_km squares before distances are taken",
            "greedy heuristic; results depend on the candidate set (ADR-0018)",
            "N3 from CP2b v5.1 (flag D); BMP and availability factors partly S",
            "farm-register residues: hub values withheld below k_min farm cells",
        ],
    }
    (out_dir / f"{stem}_meta.json").write_text(json.dumps(meta, indent=2, default=str))
    print(json.dumps(meta, indent=2, default=str))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("gpkg", type=Path)
    ap.add_argument("candidates", type=Path, help="parquet with h3_index and excluded")
    ap.add_argument("--list", action="store_true", help="print residues and facility types")
    ap.add_argument("--scenario", choices=("min", "med", "max"), default="med")
    ap.add_argument("--classes", type=Path, help="csv residue,class")
    ap.add_argument("--skip", action="append", metavar="RESIDUE")
    ap.add_argument("--radius", action="append", metavar="CLASS=R1:R2", help="road km")
    ap.add_argument("--only-to", action="append", metavar="RESIDUE=TIPO[,TIPO]")
    ap.add_argument("--q-min", type=float, help="Nm3 CH4/d a new hub must add")
    ap.add_argument("--detour-factor", type=float, help="road km per straight-line km")
    ap.add_argument("--source-cell-km", type=float, default=2.0, help="0 keeps the 1 km cells")
    ap.add_argument("--k-min", type=int, default=3)
    ap.add_argument("--chunk", type=int, default=4096, help="candidates per weight block")
    ap.add_argument("--tag", default="")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    if not args.list:
        for need in ("classes", "radius", "q_min", "detour_factor"):
            if getattr(args, need) is None:
                ap.error(f"--{need.replace('_', '-')} is required (no sourced default, ADR-0018)")
    main(args)
