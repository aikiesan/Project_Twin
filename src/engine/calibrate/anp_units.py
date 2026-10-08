"""Check the reporting scale of ANP plant-level biogas volumes against state production.

ANP open data (`anp_biometano_dados_abertos` in registry/sources.yaml) has two files:

- ``Biometano_DadosAbertos_CSV_Capacidade.csv``: per plant and month, authorised biomethane
  capacity (m³/d), biogas processing capacity (m³/d), **processed biogas** (m³/d) and
  processed / capacity (%). It is a biogas figure, not biomethane output.
- ``Biometano_DadosAbertos_CSV_Producao.csv``: biomethane production (m³ per month) per state
  and product. It does not name plants.

Some plants report processed biogas values that are about 1/1000 of their capacity for long
runs of months (Cocal Narandiba, Aug 2022 to Jul 2025: 1-30 m³/d against 51,600). That pattern
fits values reported in thousand m³/d. This module tests the hypothesis by converting
plant-level biogas to biomethane and comparing the state sum with the state production file.

The conversion uses each plant's ratio of authorised biomethane capacity to biogas processing
capacity as its upgrading yield. That is an assumption (flag D), good for an order-of-magnitude
test only. The result is evidence for or against a hypothesis; it does not correct ANP data.

Run:
    PYTHONPATH=src python -m engine.calibrate.anp_units CAPACIDADE.csv PRODUCAO.csv \
        --uf "São Paulo" --rescale NARANDIBA --start 2023-09 --end 2025-07
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

CAP_COLS = [
    "month",
    "operator",
    "cnpj",
    "region",
    "state",
    "municipality",
    "cap_biomethane_m3_d",
    "cap_biogas_m3_d",
    "biogas_processed_m3_d",
    "processed_pct",
]
PROD_COLS = ["month", "region", "state", "product", "production_m3_month"]


def _br_number(s: pd.Series) -> pd.Series:
    """Parse Brazilian decimals ("27112,00") and plain numbers ("51600", "173.037")."""
    s = s.astype(str).str.strip()
    has_comma = s.str.contains(",", regex=False)
    out = s.where(
        ~has_comma, s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    )
    return out.astype(float)


def read_capacity(path: Path | str) -> pd.DataFrame:
    """Plant-level monthly table; volumes in m³/d as published."""
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    if len(df.columns) != len(CAP_COLS):
        raise ValueError(f"{path}: expected {len(CAP_COLS)} columns, got {list(df.columns)}")
    df.columns = CAP_COLS
    for c in ["cap_biomethane_m3_d", "cap_biogas_m3_d", "biogas_processed_m3_d", "processed_pct"]:
        df[c] = _br_number(df[c])
    df["month"] = pd.to_datetime(df["month"], format="%m/%Y").dt.to_period("M")
    return df


def read_production(path: Path | str) -> pd.DataFrame:
    """State monthly production, m³ per month as published.

    In the state file a dot is the decimal separator ("4324235.558"), unlike the capacity file.
    """
    df = pd.read_csv(path, encoding="utf-8-sig", dtype=str)
    if len(df.columns) != len(PROD_COLS):
        raise ValueError(f"{path}: expected {len(PROD_COLS)} columns, got {list(df.columns)}")
    df.columns = PROD_COLS
    df["production_m3_month"] = df["production_m3_month"].astype(float)
    df["month"] = pd.to_datetime(df["month"], format="%m/%Y").dt.to_period("M")
    return df


def thousand_scale_months(cap: pd.DataFrame, max_share: float = 0.01) -> pd.DataFrame:
    """Rows with 0 < processed biogas < ``max_share`` x capacity.

    These are candidate reports in thousand m³/d.
    """
    v, c = cap["biogas_processed_m3_d"], cap["cap_biogas_m3_d"]
    return cap[(v > 0) & (v < max_share * c)]


def state_check(
    cap: pd.DataFrame,
    prod: pd.DataFrame,
    state: str,
    rescale_municipalities: tuple[str, ...] = (),
    product: str = "BIOMETANO",
    max_share: float = 0.01,
) -> pd.DataFrame:
    """Implied state biomethane (m³/month) from plant rows, as published and with rescaling.

    ``rescale_municipalities``: plants (by municipality) whose candidate thousand-scale months
    are multiplied by 1000 in the ``implied_rescaled`` column.
    Returns one row per month with ``implied_as_published``, ``implied_rescaled``,
    ``state_production`` and the two ratios to state production.
    """
    c = cap[cap["state"] == state].copy()
    days = c["month"].dt.days_in_month
    yield_ = c["cap_biomethane_m3_d"] / c["cap_biogas_m3_d"]
    c["implied_as_published"] = c["biogas_processed_m3_d"] * yield_ * days
    small = c.index.isin(thousand_scale_months(c, max_share).index)
    pick = c["municipality"].isin(rescale_municipalities) & small
    c["implied_rescaled"] = np.where(
        pick, 1000 * c["implied_as_published"], c["implied_as_published"]
    )
    out = c.groupby("month")[["implied_as_published", "implied_rescaled"]].sum()
    p = prod[(prod["state"] == state) & (prod["product"] == product)]
    out = out.join(p.set_index("month")["production_m3_month"].rename("state_production"))
    out["ratio_as_published"] = out["implied_as_published"] / out["state_production"]
    out["ratio_rescaled"] = out["implied_rescaled"] / out["state_production"]
    return out


def summarise(t: pd.DataFrame) -> pd.DataFrame:
    """Median, P10, P90 and mean |log ratio| of both ratio columns (months with production)."""
    rows = {}
    for col in ["ratio_as_published", "ratio_rescaled"]:
        r = t[col].replace([np.inf, -np.inf], np.nan).dropna()
        r = r[r > 0]
        rows[col] = {
            "months": len(r),
            "median": r.median(),
            "p10": r.quantile(0.1),
            "p90": r.quantile(0.9),
            "mean_abs_log": float(np.abs(np.log(r)).mean()),
        }
    return pd.DataFrame(rows).T


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("capacidade", type=Path)
    ap.add_argument("producao", type=Path)
    ap.add_argument("--uf", default="São Paulo")
    ap.add_argument("--rescale", nargs="*", default=[], help="municipalities to test x1000")
    ap.add_argument("--start", default=None, help="YYYY-MM")
    ap.add_argument("--end", default=None, help="YYYY-MM")
    a = ap.parse_args(argv)
    cap, prod = read_capacity(a.capacidade), read_production(a.producao)
    flagged = thousand_scale_months(cap)
    print("Candidate thousand-scale months (0 < processed < 1 % of biogas capacity):")
    print(
        flagged.groupby(["operator", "municipality"])["biogas_processed_m3_d"]
        .agg(["size", "min", "max"])
        .to_string()
    )
    t = state_check(cap, prod, a.uf, tuple(a.rescale))
    if a.start:
        t = t[t.index >= pd.Period(a.start, "M")]
    if a.end:
        t = t[t.index <= pd.Period(a.end, "M")]
    print(f"\n{a.uf}: implied biomethane vs state production (m³/month)")
    print(t.round(2).to_string())
    print("\nSummary")
    print(summarise(t).round(3).to_string())


if __name__ == "__main__":
    main()
