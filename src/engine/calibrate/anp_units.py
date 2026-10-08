"""Check the reporting scale of ANP plant-level biogas volumes against state production.

ANP open data (`anp_biometano_dados_abertos` in registry/sources.yaml) has two files:

- ``Biometano_DadosAbertos_CSV_Capacidade.csv``: per plant and month, authorised biomethane
  capacity (m³/d), biogas processing capacity (m³/d), **processed biogas** (m³/d) and
  processed / capacity (%). The label says biogas; at Cocal Narandiba the annual sums track the
  biomethane the company reports, not its biogas (docs/21 C40). No data dictionary defines it.
- ``Biometano_DadosAbertos_CSV_Producao.csv``: biomethane production (m³ per month) per state
  and product. It does not name plants.

Some plants report processed biogas values that are about 1/1000 of their capacity for long
runs of months (Cocal Narandiba, Aug 2022 to Jul 2025: 1-30 m³/d against 51,600). That pattern
fits values reported in thousand m³/d. This module tests the hypothesis by converting
plant-level biogas to biomethane and comparing the state sum with the state production file.

The conversion uses each plant's ratio of authorised biomethane capacity to biogas processing
capacity as its upgrading yield. That is an assumption (flag D), good for an order-of-magnitude
test only. The result is evidence for or against a hypothesis; it does not correct ANP data.

A second check works plant by plant: :func:`plant_period_check` sums a plant's ANP months over
each period that the owner reports (safra or calendar year, ``registry/plant_reported_annual.csv``)
and compares the sums with the reported biogas and biomethane. ANP m³ have no stated reference
conditions; the reports use Nm³ (0 °C). The ratios ignore that difference (about 7 % if ANP used
20 °C).

Run (plants keyed on CNPJ: Cocal Narandiba 14788495000170, Cocal Paraguaçu Paulista
44191268000123):
    PYTHONPATH=src python -m engine.calibrate.anp_units CAPACIDADE.csv PRODUCAO.csv \
        --uf "São Paulo" --rescale NARANDIBA --start 2023-09 --end 2025-07 \
        --reported registry/plant_reported_annual.csv \
        --plant sp_cocal_narandiba=14788495000170 \
        --plant sp_cocal_narandiba_paraguacu=14788495000170+44191268000123
"""

from __future__ import annotations

import argparse
from collections.abc import Sequence
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

#: Reported gas quantities compared with the ANP sums (``plant_reported_annual.csv``, Nm³).
REPORTED_GAS = ("biogas_produced", "biogas_to_upgrading", "biomethane_produced")


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


def read_reported(path: Path | str) -> pd.DataFrame:
    """``plant_reported_annual.csv`` with ``value`` as float and the months as periods."""
    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    df["value"] = df["value"].astype(float)
    for c in ("start_month", "end_month"):
        df[c] = pd.PeriodIndex(df[c], freq="M")
    return df


def plant_rows(cap: pd.DataFrame, keys: str | Sequence[str]) -> pd.DataFrame:
    """ANP rows of the plants named by ``keys``.

    A key is a 14-digit CNPJ (the facility key, CLAUDE.md §3) or a municipality name. A
    municipality is accepted only when all its ANP rows carry one CNPJ, so that it cannot mix
    plants (in the 2026-08 file, CAMPOS NOVOS and SAO PAULO hold two each).

    Raises:
        ValueError: if a key has no ANP rows, or a municipality key holds several CNPJs.
    """
    keys = [keys] if isinstance(keys, str) else list(keys)
    mask = np.zeros(len(cap), dtype=bool)
    for k in keys:
        if k.isdigit() and len(k) == 14:
            m = (cap["cnpj"] == k).to_numpy()
        else:
            m = (cap["municipality"] == k).to_numpy()
            n = cap.loc[m, "cnpj"].nunique()
            if n > 1:
                raise ValueError(
                    f"municipality {k!r} has {n} CNPJs in ANP; key the plant on its CNPJ"
                )
        if not m.any():
            raise ValueError(f"no ANP rows for {k!r}")
        mask |= m
    return cap[mask].copy()


def plant_period_check(
    cap: pd.DataFrame,
    reported: pd.DataFrame,
    plant_id: str,
    plants: str | Sequence[str],
    max_share: float = 0.01,
) -> pd.DataFrame:
    """ANP processed-biogas sums per reported period vs the owner's reported gas volumes.

    ``plants`` names the plant's ANP rows (:func:`plant_rows`: CNPJs or municipalities). Pass
    several when the owner reports one total for several plants (Cocal 2025/26: Narandiba +
    Paraguaçu Paulista); their ANP volumes are summed. For each period that ``reported`` holds for
    ``plant_id`` with a :data:`REPORTED_GAS` quantity, the ANP daily values are multiplied by
    the days in the month and summed, as published and with the candidate thousand-scale
    months (:func:`thousand_scale_months`) ×1000.

    Returns one row per period: ``period_kind``, ``period``, ``months_in_period``,
    ``anp_months`` (months with at least one ANP row), ``anp_m3_as_published``,
    ``anp_m3_rescaled``, and for each reported gas quantity ``q``: ``reported_<q>_nm3`` and
    ``ratio_rescaled_to_<q>`` (NaN when not reported).

    Raises:
        ValueError: if :func:`plant_rows` refuses a key, or two reported values for the same
            period and quantity differ (log the conflict in docs/21 and drop one row by hand;
            never average).
    """
    a = plant_rows(cap, plants)
    small = a.index.isin(thousand_scale_months(a, max_share).index)
    vol = a["biogas_processed_m3_d"] * a["month"].dt.days_in_month
    a["vol_pub"] = vol
    a["vol_resc"] = np.where(small, 1000 * vol, vol)
    r = reported[(reported["plant_id"] == plant_id) & reported["quantity"].isin(REPORTED_GAS)]
    keys = ["period_kind", "period", "start_month", "end_month"]
    rows = []
    for _, p in r[keys].drop_duplicates().sort_values(["start_month", "period_kind"]).iterrows():
        win = a[(a["month"] >= p["start_month"]) & (a["month"] <= p["end_month"])]
        row = {
            "period_kind": p["period_kind"],
            "period": p["period"],
            "months_in_period": (p["end_month"] - p["start_month"]).n + 1,
            "anp_months": win["month"].nunique(),
            "anp_m3_as_published": float(win["vol_pub"].sum()),
            "anp_m3_rescaled": float(win["vol_resc"].sum()),
        }
        in_period = r[(r["period_kind"] == p["period_kind"]) & (r["period"] == p["period"])]
        for q in REPORTED_GAS:
            vals = in_period.loc[in_period["quantity"] == q, "value"].unique()
            if len(vals) > 1:
                raise ValueError(
                    f"{plant_id} {p['period']} {q}: reported values differ {list(vals)}; "
                    "log the conflict in docs/21 and keep one row for this check"
                )
            v = float(vals[0]) if len(vals) else np.nan
            row[f"reported_{q}_nm3"] = v
            row[f"ratio_rescaled_to_{q}"] = row["anp_m3_rescaled"] / v if v > 0 else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


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
    ap.add_argument(
        "--reported", type=Path, default=None, help="plant_reported_annual.csv for the plant check"
    )
    ap.add_argument(
        "--plant",
        action="append",
        default=[],
        metavar="PLANT_ID=KEY[+KEY]",
        help=(
            "plant to check against --reported; KEY is a CNPJ or a municipality with one CNPJ, "
            "e.g. sp_cocal_narandiba=14788495000170; join keys with + when the owner reports "
            "one total for several plants"
        ),
    )
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
    if a.reported is not None:
        reported = read_reported(a.reported)
        for spec in a.plant:
            plant_id, _, keys = spec.partition("=")
            pc = plant_period_check(cap, reported, plant_id, keys.split("+"))
            print(f"\n{plant_id} ({keys}): ANP sums vs owner-reported volumes")
            print(pc.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
