"""N3 CH₄ within 30 km of each suitability-grid cell, from the CP2b v5.1 1 km supply grid.

ADR-0017 criterion. Reads ``grade_oferta_1km.gpkg`` (registry ``esd_n3_supply_grid_1km``;
layers ``celulas`` and ``pontos``, columns ``<RESIDUE>__min|med|max`` in Nm³ CH₄/d of N3) and
``suitability_grid_v0.parquet`` (H3 cells), and writes next to the grid:

- ``n3_ch4_30km_<scenario>.parquet``: per H3 cell, ``ch4_n3_nm3_d_30km`` (all residues),
  ``ch4_n3_nonfarm_nm3_d_30km``, ``ch4_n3_farm_nm3_d_30km`` and ``farm_cells_30km``;
- ``n3_ch4_30km_<scenario>_meta.json``: input sha256, totals check, suppression counts.

LGPD (sources.yaml ``esd_n3_supply_grid_1km``): the five farm-register residues (poultry,
swine, dairy and feedlot cattle) enter only as 30 km sums, and only where at least ``--k-min``
1 km cells with a farm value fall inside the radius (a cell with a value holds at least one farm
or a fallback point). Below that, the farm part is withheld (NaN, ``farm_suppressed``) and
``ch4_n3_nm3_d_30km`` carries the non-farm part only. Nothing is written cell by cell from the
gpkg. Outputs stay in ``data/`` (never in git).

Run (needs shapely, pyproj, pyogrio):
    PYTHONPATH=src python scripts/siting/n3_ch4_30km.py <grade_oferta_1km.gpkg> <grid folder>
        [--scenario med] [--radius-km 30] [--k-min 3]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import h3
import numpy as np
import pandas as pd

from engine.siting.catchment import disc_sums

FARM = ("AVES_CORTE", "AVES_POSTURA", "SUINOS", "BOV_LEITE", "BOV_CONFINADO")
CELL_M = 1000.0  # grade.celula_oferta_m in the ESD config_fl.yaml


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_layer(path: Path, layer: str, scenario: str):
    """Centroid x, y (layer CRS, m), the ``<RESIDUE>__<scenario>`` table and the CRS."""
    import pyogrio
    import shapely

    meta, _, geom, fields = pyogrio.raw.read(path, layer=layer, read_geometry=True)
    names = list(meta["fields"])
    suffix = f"__{scenario}"
    cols = {n[: -len(suffix)]: i for i, n in enumerate(names) if n.endswith(suffix)}
    if not cols:
        raise KeyError(f"{layer}: no column ending in {suffix!r}")
    tab = pd.DataFrame({r: np.asarray(fields[i], float) for r, i in cols.items()})
    c = shapely.centroid(shapely.from_wkb(geom))
    return shapely.get_x(c), shapely.get_y(c), tab, meta.get("crs")


def main(gpkg: Path, folder: Path, scenario: str, radius_km: float, k_min: int) -> None:
    from pyproj import CRS, Transformer

    xs, ys, tabs, crs = [], [], [], None
    for layer in ("celulas", "pontos"):
        x, y, t, c = read_layer(gpkg, layer, scenario)
        xs.append(x), ys.append(y), tabs.append(t)
        crs = crs or c
    x, y = np.concatenate(xs), np.concatenate(ys)
    tab = pd.concat(tabs, ignore_index=True).fillna(0.0)
    farm = [r for r in tab.columns if r in FARM]
    other = [r for r in tab.columns if r not in FARM]

    grid = pd.read_parquet(folder / "suitability_grid_v0.parquet", columns=["h3_index"])
    lat, lon = map(np.array, zip(*(h3.cell_to_latlng(c) for c in grid["h3_index"]), strict=True))
    to_m = Transformer.from_crs("EPSG:4326", CRS.from_user_input(crs), always_xy=True)
    qx, qy = to_m.transform(lon, lat)

    vals = np.c_[
        tab[other].sum(axis=1),
        tab[farm].sum(axis=1),
        (tab[farm].sum(axis=1) > 0).astype(float),
    ]
    s = disc_sums(x, y, vals, qx, qy, radius_m=radius_km * 1000, cell_m=CELL_M)
    nonfarm, farm_sum, farm_cells = s[:, 0], s[:, 1], np.rint(s[:, 2]).astype(int)
    suppressed = (farm_cells > 0) & (farm_cells < k_min)
    farm_out = np.where(suppressed, np.nan, farm_sum)
    out = pd.DataFrame(
        {
            "h3_index": grid["h3_index"].to_numpy(),
            "ch4_n3_nm3_d_30km": nonfarm + np.nan_to_num(farm_out),
            "ch4_n3_nonfarm_nm3_d_30km": nonfarm,
            "ch4_n3_farm_nm3_d_30km": farm_out,
            "farm_cells_30km": farm_cells,
            "farm_suppressed": suppressed,
        }
    )
    stem = f"n3_ch4_30km_{scenario}"
    out.to_parquet(folder / f"{stem}.parquet", index=False)

    total = float(tab.to_numpy().sum())
    meta = {
        "input": {"file": gpkg.name, "sha256": sha256(gpkg), "crs": str(crs)},
        "scenario": scenario,
        "radius_km": radius_km,
        "cell_m": CELL_M,
        "k_min_farm_cells": k_min,
        "residues_farm": farm,
        "residues_other": other,
        "gpkg_total_nm3_ch4_d": round(total, 1),
        "gpkg_total_expected_med": 19183201 if scenario == "med" else None,
        "h3_cells": int(len(out)),
        "farm_suppressed_cells": int(suppressed.sum()),
        "quantiles_ch4_n3_nm3_d_30km": {
            str(q): round(float(out["ch4_n3_nm3_d_30km"].quantile(q)), 1)
            for q in (0.05, 0.25, 0.5, 0.75, 0.95, 0.99)
        },
        "caveats": [
            "straight-line radius on cell centres (1 km), not road network",
            "N3 from CP2b v5.1 (flag D); BMP and availability factors partly S",
            "farm-register residues withheld where fewer than k_min farm cells in the radius",
        ],
    }
    (folder / f"{stem}_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("gpkg", type=Path)
    ap.add_argument("folder", type=Path)
    ap.add_argument("--scenario", choices=("min", "med", "max"), default="med")
    ap.add_argument("--radius-km", type=float, default=30.0)
    ap.add_argument("--k-min", type=int, default=3)
    a = ap.parse_args()
    main(a.gpkg, a.folder, a.scenario, a.radius_km, a.k_min)
