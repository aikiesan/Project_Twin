"""Feed-to-gas check: do the registry's yields explain a plant's reported biogas? (docs/13 §9)

A plant owner reports, per period, the feed it digested and the biogas it made
(``registry/plant_reported_annual.csv``). This module computes the CH₄ that the reported vinasse
and filter cake give with the registry's central yields
(:func:`engine.process.mass_balance.substrates_from_registry`), turns it into biogas with the CH₄
fraction of the biogas, and compares the result with the reported biogas.

Outputs per period and CH₄ fraction:

- ``explained_share``: modelled biogas / reported biogas. Co-feeds with no registry substrate
  (manure as reported, "other industrial and urban waste") are left out; their tonnage is shown,
  and ``cofeed_nm3_biogas_per_t`` is the yield they would need to close the gap on their own.
- closure values (:func:`closure_values`): for each yield parameter, the value that closes the
  gap when the other parameters stay at their central values. CH₄ is proportional to each of
  them. A closure value outside the registry's low-high range means that parameter alone cannot
  explain the plant.

Assumptions (flag D, docs/08): conversion is complete within the HRT (the registry has no
first-order rate for these substrates) and the BMP is scaled by ``bmp_fullscale``; the vinasse
volume is used as reported, in m³; the CH₄ fraction is in conflict (docs/21 C13), so both values
run. Where the owner reports both, ``biomethane_per_upgrading_biogas`` is reported biomethane /
reported biogas sent to upgrading, which equals x_CH4 × CH₄ recovery / CH₄ content of the
biomethane.

Run:
    PYTHONPATH=src python -m engine.calibrate.plant_yield registry/plant_reported_annual.csv \
        --plant sp_cocal_narandiba
"""

from __future__ import annotations

import argparse
import math
from collections.abc import Mapping, Sequence
from pathlib import Path

import numpy as np
import pandas as pd

from engine.calibrate.anp_units import read_reported
from engine.process.mass_balance import Substrate, substrates_from_registry
from engine.registry import Param, load_parameters

#: Reported feed quantities this check models: quantity -> (substrate, reported unit).
MODELLED_FEED = {
    "vinasse_processed": ("vinasse", "m3"),
    "filter_cake_processed": ("filter_cake", "t"),
}

#: Reported feed quantities with no registry substrate: left out, tonnage shown.
UNMODELLED_FEED = ("cattle_manure_processed", "chicken_manure_processed", "other_waste_processed")

#: CH₄ fractions of vinasse + filter cake biogas in conflict (docs/21 C13): CP2B note vs
#: PILAR-2b feedstocks.yaml. Same pair as the skeleton runner (``--x-ch4``).
X_CH4_C13 = (0.575, 0.65)

#: Yield parameters per substrate; the substrate's CH₄ is proportional to each of them.
YIELD_PARAMS = {
    "vinasse": ("vin_cod", "cod_removal", "vin_ch4_yield"),
    "filter_cake": ("fc_bmp", "bmp_fullscale"),
}

#: Composite row per substrate in :func:`closure_values`: CH₄ per unit of reported feed.
COMPOSITE = {
    "vinasse": ("vinasse_ch4_per_m3", "Nm3 CH4 per m3"),
    "filter_cake": ("filter_cake_ch4_per_t_fm", "Nm3 CH4 per t FM"),
}


def _one_value(g: pd.DataFrame, quantity: str, label: str) -> float:
    """The single reported value of ``quantity`` in ``g`` (NaN if absent)."""
    vals = g.loc[g["quantity"] == quantity, "value"].unique()
    if len(vals) > 1:
        raise ValueError(
            f"{label} {quantity}: reported values differ {list(vals)}; "
            "log the conflict in docs/21 and keep one row for this check"
        )
    return float(vals[0]) if len(vals) else math.nan


def feed_to_gas(
    reported: pd.DataFrame,
    plant_id: str,
    substrates: Mapping[str, Substrate],
    bmp_fullscale: float,
    x_ch4: Sequence[float] = X_CH4_C13,
) -> pd.DataFrame:
    """Modelled vs reported biogas for each period with reported biogas.

    Args:
        reported: :func:`engine.calibrate.anp_units.read_reported` table.
        plant_id: plant (or plant group) as keyed in ``reported``.
        substrates: needs ``"vinasse"`` and ``"filter_cake"``
            (:func:`~engine.process.mass_balance.substrates_from_registry`).
        bmp_fullscale: BMP to full-scale factor (registry ``bmp_fullscale``).
        x_ch4: CH₄ fractions of the biogas to run.

    Returns:
        One row per period and ``x_ch4``: reported feed (``vinasse_m3``, ``filter_cake_t``,
        ``unmodelled_feed_t``), ``ch4_vinasse_nm3``, ``ch4_filter_cake_nm3``,
        ``biogas_modelled_nm3``, ``biogas_reported_nm3``, ``explained_share``,
        ``cofeed_nm3_biogas_per_t``, ``biomethane_per_upgrading_biogas`` and ``note``. A period
        with reported biogas but without both modelled feeds keeps NaN gas columns and a note.

    Raises:
        ValueError: if the plant has no rows, or two reported values for the same period and
            quantity differ.
    """
    r = reported[reported["plant_id"] == plant_id]
    if r.empty:
        raise ValueError(f"no reported rows for plant {plant_id!r}")
    rows = []
    for (kind, period, start), g in r.groupby(["period_kind", "period", "start_month"], sort=False):
        label = f"{plant_id} {kind} {period}"
        biogas = _one_value(g, "biogas_produced", label)
        if math.isnan(biogas):
            continue
        feed = {q: _one_value(g, q, label) for q in MODELLED_FEED}
        unmodelled = [_one_value(g, q, label) for q in UNMODELLED_FEED]
        unmodelled_t = float(np.nansum(unmodelled))
        missing = [q for q, v in feed.items() if math.isnan(v)]
        ch4 = {}
        for q, (name, _unit) in MODELLED_FEED.items():
            s = substrates[name]
            amount = feed[q]
            fresh_t = amount * s.density_t_per_m3 if MODELLED_FEED[q][1] == "m3" else amount
            ch4[name] = math.nan if missing else s.ch4_nm3(fresh_t, math.inf, bmp_fullscale)
        bm = _one_value(g, "biomethane_produced", label)
        to_upg = _one_value(g, "biogas_to_upgrading", label)
        for x in x_ch4:
            modelled = (ch4["vinasse"] + ch4["filter_cake"]) / x
            gap = biogas - modelled
            rows.append(
                {
                    "period_kind": kind,
                    "period": period,
                    "start_month": start,
                    "x_ch4": x,
                    "vinasse_m3": feed["vinasse_processed"],
                    "filter_cake_t": feed["filter_cake_processed"],
                    "unmodelled_feed_t": unmodelled_t,
                    "ch4_vinasse_nm3": ch4["vinasse"],
                    "ch4_filter_cake_nm3": ch4["filter_cake"],
                    "biogas_modelled_nm3": modelled,
                    "biogas_reported_nm3": biogas,
                    "explained_share": modelled / biogas,
                    "cofeed_nm3_biogas_per_t": gap / unmodelled_t if unmodelled_t > 0 else math.nan,
                    "biomethane_per_upgrading_biogas": bm / to_upg if to_upg > 0 else math.nan,
                    "note": f"feed not reported: {', '.join(missing)}" if missing else "",
                }
            )
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    return out.sort_values(["start_month", "period_kind", "x_ch4"]).reset_index(drop=True)


def closure_values(table: pd.DataFrame, params: Mapping[str, Param]) -> pd.DataFrame:
    """Value of each yield parameter that alone closes the biogas gap (others at central).

    For a vinasse parameter ``p``: ``p* = p × (biogas_reported × x − CH₄_cake) / CH₄_vinasse``;
    for a filter-cake parameter the roles swap. ``in_range`` says whether ``p*`` lies within the
    registry's low-high range. Each substrate also gets one composite row, its CH₄ per unit of
    reported feed (``vinasse_ch4_per_m3``, ``filter_cake_ch4_per_t_fm``; flag D, no range): the
    value that closes the gap whatever mix of its parameters moves (TS and VS/TS included).
    Rows without modelled CH₄ are skipped.
    """
    rows = []
    for _, t in table.dropna(subset=["ch4_vinasse_nm3", "ch4_filter_cake_nm3"]).iterrows():
        need = t["biogas_reported_nm3"] * t["x_ch4"]
        own = {"vinasse": t["ch4_vinasse_nm3"], "filter_cake": t["ch4_filter_cake_nm3"]}
        amount = {"vinasse": t["vinasse_m3"], "filter_cake": t["filter_cake_t"]}
        for sub, pids in YIELD_PARAMS.items():
            other = own["filter_cake" if sub == "vinasse" else "vinasse"]
            factor = (need - other) / own[sub] if own[sub] > 0 else math.nan
            per_unit = own[sub] / amount[sub] if amount[sub] > 0 else math.nan
            rows.append(
                {
                    "period_kind": t["period_kind"],
                    "period": t["period"],
                    "x_ch4": t["x_ch4"],
                    "param": COMPOSITE[sub][0],
                    "unit": COMPOSITE[sub][1],
                    "flag": "D",
                    "central": per_unit,
                    "low": math.nan,
                    "high": math.nan,
                    "closure": per_unit * factor,
                    "in_range": None,
                }
            )
            for pid in pids:
                p = params[pid]
                c = p.require_central()
                star = c * factor
                rows.append(
                    {
                        "period_kind": t["period_kind"],
                        "period": t["period"],
                        "x_ch4": t["x_ch4"],
                        "param": pid,
                        "unit": p.unit,
                        "flag": p.confidence,
                        "central": c,
                        "low": p.low,
                        "high": p.high,
                        "closure": star,
                        "in_range": (
                            bool(p.low <= star <= p.high)
                            if p.has_range and not math.isnan(star)
                            else None
                        ),
                    }
                )
    return pd.DataFrame(rows)


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("reported", type=Path, help="registry/plant_reported_annual.csv")
    ap.add_argument("--plant", action="append", required=True, help="plant_id (repeatable)")
    ap.add_argument(
        "--x-ch4", type=float, nargs="+", default=list(X_CH4_C13), help="CH4 fractions to run"
    )
    a = ap.parse_args(argv)
    params = load_parameters()
    # The density cancels here: vinasse is on a COD basis per m³ and filter cake is reported in t.
    subs = substrates_from_registry(params, fresh_density_t_per_m3=1.0)
    bmp_fs = params["bmp_fullscale"].require_central()
    reported = read_reported(a.reported)
    pd.set_option("display.width", 200)
    for plant in a.plant:
        t = feed_to_gas(reported, plant, subs, bmp_fs, a.x_ch4)
        print(f"\n{plant}: modelled (vinasse + filter cake, registry central) vs reported biogas")
        cols = [
            "period_kind",
            "period",
            "x_ch4",
            "vinasse_m3",
            "filter_cake_t",
            "unmodelled_feed_t",
            "biogas_modelled_nm3",
            "biogas_reported_nm3",
            "explained_share",
            "cofeed_nm3_biogas_per_t",
            "biomethane_per_upgrading_biogas",
            "note",
        ]
        print(t[cols].round(3).to_string(index=False))
        c = closure_values(t, params)
        if not c.empty:
            print(f"\n{plant}: closure value of each yield parameter (others at central)")
            print(c.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
