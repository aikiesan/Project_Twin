"""Ceiling of urban-residue CH₄ in SP (N3, CP2b v5.1) and how few municipalities hold it.

Reads ``grade_oferta_1km.gpkg`` (registry ``esd_n3_supply_grid_1km``) and the H3 grid
``suitability_grid_v0.parquet`` (for the IBGE code of each 1 km cell). Writes to the grid folder:

- ``urban_ceiling_statewide.csv``: N3 per residue and scenario (Nm³ CH₄/d), all 16 residues, with
  the urban group (RSU_ORGANICO, PODA_URBANA, LODO_ETE) flagged, and its share of the total;
- ``urban_ceiling_municipal.csv``: urban N3 per municipality (min/med/max and per residue, med),
  rank and cumulative share of the state's urban N3 med;
- ``urban_ceiling_meta.json``: input sha256, totals, municipalities needed for 50/80/90 %.

Only non-farm residues are written per municipality; the farm-register residues enter the
statewide totals only (LGPD, sources.yaml ``esd_n3_supply_grid_1km``).

N3 is the CP2b *mobilisable* CH₄ potential (flag D). It is not landfill-gas recovery from existing
landfills, which depends on decay over years and collection efficiency, nor biomethane plant
capacity. Compare with plant capacities as an order of magnitude only.

Run (needs shapely, pyproj, pyogrio):
    PYTHONPATH=src python scripts/supply/urban_ceiling.py <grade_oferta_1km.gpkg> <grid folder>
        [--names municipal_panel_v0.csv]
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

from engine.ingest.municipalities import name_map
from engine.supply.concentration import count_for_share, cumulative_share

URBAN = ("RSU_ORGANICO", "PODA_URBANA", "LODO_ETE")
FARM = ("AVES_CORTE", "AVES_POSTURA", "SUINOS", "BOV_LEITE", "BOV_CONFINADO")
SCENARIOS = ("min", "med", "max")
SHARES = (0.5, 0.8, 0.9)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def read_layer(path: Path, layer: str):
    """Centroids (layer CRS), ``<RESIDUE>__<scenario>`` table, ``ibge`` field (if any), CRS."""
    import pyogrio
    import shapely

    meta, _, geom, fields = pyogrio.raw.read(path, layer=layer, read_geometry=True)
    names = list(meta["fields"])
    cols = {n: i for i, n in enumerate(names) if "__" in n and n.split("__")[1] in SCENARIOS}
    tab = pd.DataFrame({n: np.asarray(fields[i], float) for n, i in cols.items()}).fillna(0.0)
    ibge = (
        pd.to_numeric(pd.Series(fields[names.index("ibge")]), errors="coerce")
        if "ibge" in names
        else None
    )
    c = shapely.centroid(shapely.from_wkb(geom))
    return shapely.get_x(c), shapely.get_y(c), tab, ibge, meta.get("crs")


def main(gpkg: Path, folder: Path, names: Path | None) -> None:
    from pyproj import CRS, Transformer

    grid = pd.read_parquet(
        folder / "suitability_grid_v0.parquet", columns=["h3_index", "ibge_code"]
    )
    res = h3.get_resolution(grid["h3_index"].iloc[0])
    code_of = dict(
        zip(grid["h3_index"], pd.to_numeric(grid["ibge_code"], errors="coerce"), strict=True)
    )

    parts = []
    for layer in ("celulas", "pontos"):
        x, y, tab, ibge, crs = read_layer(gpkg, layer)
        to_ll = Transformer.from_crs(CRS.from_user_input(crs), "EPSG:4326", always_xy=True)
        lon, lat = to_ll.transform(x, y)
        via_h3 = pd.Series(
            [code_of.get(h3.latlng_to_cell(a, o, res)) for a, o in zip(lat, lon, strict=True)],
            dtype=float,
        )
        tab["ibge_code"] = via_h3 if ibge is None else ibge.where(ibge.notna(), via_h3)
        tab["layer"] = layer
        parts.append(tab)
    t = pd.concat(parts, ignore_index=True)
    vcols = [c for c in t.columns if "__" in c]

    # Statewide, every residue (aggregate only).
    st = t[vcols].sum().rename("nm3_ch4_d").reset_index()
    st[["residue", "scenario"]] = st["index"].str.split("__", expand=True)
    st = st.pivot(index="residue", columns="scenario", values="nm3_ch4_d")[list(SCENARIOS)]
    st.columns = [f"n3_{s}_nm3_ch4_d" for s in SCENARIOS]
    st["group"] = np.where(
        st.index.isin(URBAN), "urban", np.where(st.index.isin(FARM), "farm", "agro")
    )
    for s in SCENARIOS:
        st[f"share_{s}"] = st[f"n3_{s}_nm3_ch4_d"] / st[f"n3_{s}_nm3_ch4_d"].sum()
    st = st.sort_values(["group", "n3_med_nm3_ch4_d"], ascending=[False, False])
    st.round(4).to_csv(folder / "urban_ceiling_statewide.csv")

    # Per municipality, urban residues only.
    ucols = [f"{r}__{s}" for r in URBAN for s in SCENARIOS if f"{r}__{s}" in t]
    m = t.groupby("ibge_code")[ucols].sum()
    for s in SCENARIOS:
        m[f"urban_{s}_nm3_ch4_d"] = m[[c for c in ucols if c.endswith(f"__{s}")]].sum(axis=1)
    keep = [f"urban_{s}_nm3_ch4_d" for s in SCENARIOS] + [f"{r}__med" for r in URBAN]
    m = m[keep].rename(columns={f"{r}__med": f"{r.lower()}_med_nm3_ch4_d" for r in URBAN})
    cs = cumulative_share(m["urban_med_nm3_ch4_d"])
    m = m.join(cs[["rank", "cum_share"]]).sort_values("rank")
    m.index = m.index.astype("Int64")
    if names is not None:
        m.insert(0, "municipio", m.index.map(name_map(names)).fillna(""))
    m.round(4).to_csv(folder / "urban_ceiling_municipal.csv")

    urban_tot = {
        s: float(st.loc[st["group"] == "urban", f"n3_{s}_nm3_ch4_d"].sum()) for s in SCENARIOS
    }
    unassigned = {
        s: round(
            float(t.loc[t["ibge_code"].isna(), [c for c in ucols if c.endswith(s)]].sum().sum()), 1
        )
        for s in SCENARIOS
    }
    meta = {
        "input": {"file": gpkg.name, "sha256": sha256(gpkg)},
        "names": None if names is None else {"file": names.name, "sha256": sha256(names)},
        "n3_total_nm3_ch4_d": {
            s: round(float(st[f"n3_{s}_nm3_ch4_d"].sum()), 1) for s in SCENARIOS
        },
        "urban_total_nm3_ch4_d": {s: round(v, 1) for s, v in urban_tot.items()},
        "urban_share_of_n3": {
            s: round(urban_tot[s] / float(st[f"n3_{s}_nm3_ch4_d"].sum()), 4) for s in SCENARIOS
        },
        "urban_by_residue_med_nm3_ch4_d": {
            r: round(float(st.loc[r, "n3_med_nm3_ch4_d"]), 1) for r in URBAN if r in st.index
        },
        "urban_unassigned_to_municipality_nm3_ch4_d": unassigned,
        "municipalities_with_urban_n3": int((m["urban_med_nm3_ch4_d"] > 0).sum()),
        "municipalities_for_share_of_urban_med": {
            str(k): v for k, v in count_for_share(m["urban_med_nm3_ch4_d"], SHARES).items()
        },
        "caveats": [
            "N3 = CP2b v5.1 mobilisable CH4 potential (flag D), not landfill-gas recovery",
            "units: Nm3 CH4 per day (not biogas, not biomethane)",
            "1 km cells assigned to a municipality through the H3 grid cell of their centroid",
        ],
    }
    (folder / "urban_ceiling_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))
    print("\nStatewide N3 by residue (Nm3 CH4/d):")
    print(st.round(3).to_string())
    print("\nTop 25 municipalities by urban N3 med:")
    print(m.head(25).round(3).to_string())


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("gpkg", type=Path)
    ap.add_argument("folder", type=Path)
    ap.add_argument("--names", type=Path)
    a = ap.parse_args()
    for label, p in {"gpkg": a.gpkg, "--names": a.names}.items():
        if p is not None and not p.is_file():
            raise SystemExit(f"{label}: not a file: {str(p)!r} (empty shell variable?)")
    main(a.gpkg, a.folder, a.names)
