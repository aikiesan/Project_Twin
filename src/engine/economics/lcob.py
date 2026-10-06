"""LCOB v0: levelized cost of biomethane in annuity form (docs/11 §2).

This is the economics step of the walking skeleton (ADR-0010)::

    LCOB = (CAPEX · CRF + OPEX + F + T − R_co) / E,   CRF = r(1+r)^n / ((1+r)^n − 1)

with CAPEX the investment (R$), OPEX the O&M per year (fixed R$/yr plus variable R$/Nm³ × E),
F feedstock and T transport costs per year, R_co co-product revenue per year, E the biomethane
delivered per year (Nm³) and r the real discount rate over n years. Delivered biomethane, not
nameplate, is the denominator, so a low capacity factor raises the LCOB.

v0 limits, stated here so they show in every result:

- one CAPEX at year 0, constant real costs and output, no replacement of the upgrading unit;
- no price-year escalation: the registry values are used in their own price years (the EPE
  CAPEX is in R$ of Dec 2024 per the radar digest of 2026-10-06; docs/21 C15);
- no taxes, financing structure or revenues other than a co-product credit.

Units: R$ (BRL, real), Nm³ (0 °C, 1 atm), rates as fractions per year. Conversions to US$/MMBtu
take the heating value and the exchange rate as explicit arguments.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

import pandas as pd

from engine.registry import Param, load_parameters

#: MJ per MMBtu: 10⁶ Btu (International Table), 1 Btu = 1055.05585262 J.
MJ_PER_MMBTU = 1055.05585262


def crf(rate: float, years: int) -> float:
    """Capital recovery factor for a real ``rate`` (fraction per year) over ``years``."""
    if years <= 0:
        raise ValueError("years must be > 0")
    if rate < 0:
        raise ValueError("rate must be >= 0")
    if rate == 0:
        return 1.0 / years
    growth = (1.0 + rate) ** years
    return rate * growth / (growth - 1.0)


def capex_brl(
    nameplate_nm3_d: float,
    specific_brl_per_nm3_d: float,
    *,
    ref_capacity_nm3_d: float | None = None,
    scale_exp: float | None = None,
) -> float:
    """Investment from a specific CAPEX (R$ per Nm³/d of biomethane nameplate).

    Without a reference capacity the CAPEX is linear: ``specific × nameplate``. With
    ``ref_capacity_nm3_d`` and ``scale_exp`` it follows the power law
    ``specific × ref × (nameplate / ref) ** scale_exp`` (registry ``scale_exp``).
    """
    if nameplate_nm3_d <= 0 or specific_brl_per_nm3_d < 0:
        raise ValueError("nameplate_nm3_d must be > 0 and specific_brl_per_nm3_d >= 0")
    if (ref_capacity_nm3_d is None) != (scale_exp is None):
        raise ValueError("give both ref_capacity_nm3_d and scale_exp, or neither")
    if ref_capacity_nm3_d is None:
        return specific_brl_per_nm3_d * nameplate_nm3_d
    if ref_capacity_nm3_d <= 0:
        raise ValueError("ref_capacity_nm3_d must be > 0")
    return (
        specific_brl_per_nm3_d
        * ref_capacity_nm3_d
        * (nameplate_nm3_d / ref_capacity_nm3_d) ** scale_exp  # type: ignore[operator]
    )


@dataclass(frozen=True)
class LcobResult:
    """LCOB and its components, all in R$ per Nm³ of delivered biomethane.

    ``coproduct_brl_per_nm3`` is a credit: ``lcob = capex + opex + feedstock + transport −
    coproduct``.
    """

    lcob_brl_per_nm3: float
    capex_brl_per_nm3: float
    opex_brl_per_nm3: float
    feedstock_brl_per_nm3: float
    transport_brl_per_nm3: float
    coproduct_brl_per_nm3: float
    annual_biomethane_nm3: float
    annualized_capex_brl: float
    crf: float


def lcob_annuity(
    *,
    capex: float,
    annual_biomethane_nm3: float,
    rate: float,
    years: int,
    opex_fixed_brl_per_yr: float = 0.0,
    opex_var_brl_per_nm3: float = 0.0,
    feedstock_brl_per_yr: float = 0.0,
    transport_brl_per_yr: float = 0.0,
    coproduct_brl_per_yr: float = 0.0,
) -> LcobResult:
    """Annuity LCOB (docs/11 §2) for one plant and one representative year.

    Args:
        capex: investment, R$.
        annual_biomethane_nm3: biomethane delivered per year, Nm³ (from the process module).
        rate: real discount rate, fraction per year.
        years: economic lifetime.
        opex_fixed_brl_per_yr, opex_var_brl_per_nm3: O&M, fixed and per delivered Nm³.
        feedstock_brl_per_yr, transport_brl_per_yr: costs per year (negative = gate fee).
        coproduct_brl_per_yr: co-product revenue per year (digestate, CO₂), subtracted.
    """
    if annual_biomethane_nm3 <= 0:
        raise ValueError("annual_biomethane_nm3 must be > 0; LCOB is undefined without output")
    if capex < 0:
        raise ValueError("capex must be >= 0")
    f = crf(rate, years)
    e = float(annual_biomethane_nm3)
    annual_capex = float(capex) * f
    opex = opex_fixed_brl_per_yr / e + opex_var_brl_per_nm3
    parts = {
        "capex": annual_capex / e,
        "opex": opex,
        "feedstock": feedstock_brl_per_yr / e,
        "transport": transport_brl_per_yr / e,
        "coproduct": coproduct_brl_per_yr / e,
    }
    parts = {k: float(v) for k, v in parts.items()}
    total = parts["capex"] + parts["opex"] + parts["feedstock"] + parts["transport"]
    return LcobResult(
        lcob_brl_per_nm3=total - parts["coproduct"],
        capex_brl_per_nm3=parts["capex"],
        opex_brl_per_nm3=parts["opex"],
        feedstock_brl_per_nm3=parts["feedstock"],
        transport_brl_per_nm3=parts["transport"],
        coproduct_brl_per_nm3=parts["coproduct"],
        annual_biomethane_nm3=e,
        annualized_capex_brl=annual_capex,
        crf=f,
    )


def brl_per_nm3_to_usd_per_mmbtu(
    value_brl_per_nm3: float, *, hhv_mj_per_nm3: float, brl_per_usd: float
) -> float:
    """Convert R$/Nm³ to US$/MMBtu with an explicit heating value and exchange rate."""
    if hhv_mj_per_nm3 <= 0 or brl_per_usd <= 0:
        raise ValueError("hhv_mj_per_nm3 and brl_per_usd must be > 0")
    return value_brl_per_nm3 / brl_per_usd / hhv_mj_per_nm3 * MJ_PER_MMBTU


# --- registry builders ------------------------------------------------------------------------


@dataclass(frozen=True)
class EconomicInputs:
    """Registry values the v0 LCOB uses, with the ids they came from."""

    specific_capex_brl_per_nm3_d: float
    opex_var_brl_per_nm3: float
    rate: float
    years: int
    param_ids: tuple[str, ...] = field(default=())


def economics_from_registry(
    params: Mapping[str, Param] | None = None, *, capex_id: str = "capex_epe"
) -> EconomicInputs:
    """Central values: specific CAPEX (``capex_id``), ``opex_epe``, ``wacc_real``, ``plant_life``.

    ``capex_id`` picks the specific-CAPEX row (``capex_epe``, ``capex_large_vin``,
    ``capex_small_vin`` …); all are in R$ per Nm³/d of biomethane nameplate.
    """
    p = params if params is not None else load_parameters()
    if capex_id not in p:
        raise KeyError(f"{capex_id!r} is not in the registry")
    years = p["plant_life"].require_central()
    if years != int(years):
        raise ValueError(f"plant_life must be a whole number of years, got {years}")
    return EconomicInputs(
        specific_capex_brl_per_nm3_d=p[capex_id].require_central(),
        opex_var_brl_per_nm3=p["opex_epe"].require_central(),
        rate=p["wacc_real"].require_central() / 100,  # % per yr -> fraction
        years=int(years),
        param_ids=(capex_id, "opex_epe", "wacc_real", "plant_life"),
    )


def lcob_from_registry(
    nameplate_nm3_d: float,
    annual_biomethane_nm3: float,
    params: Mapping[str, Param] | None = None,
    *,
    capex_id: str = "capex_epe",
) -> LcobResult:
    """v0 LCOB: linear CAPEX from ``capex_id`` × nameplate, EPE OPEX per Nm³, registry WACC."""
    econ = economics_from_registry(params, capex_id=capex_id)
    return lcob_annuity(
        capex=capex_brl(nameplate_nm3_d, econ.specific_capex_brl_per_nm3_d),
        annual_biomethane_nm3=annual_biomethane_nm3,
        rate=econ.rate,
        years=econ.years,
        opex_var_brl_per_nm3=econ.opex_var_brl_per_nm3,
    )


#: LCOB anchors from the registry (docs/11 §8): id → note on the comparison basis.
ANCHORS = {
    "lcob_epe_sucro": "EPE, sugar-energy plant at a 2 Mt/yr mill; m³ basis not stated, "
    "compared as Nm³",
    "lcob_fiesp": "FIESP-led study (June 2025), SP production cost without taxes or logistics",
}


def compare_with_anchors(
    lcob_brl_per_nm3: float,
    *,
    brl_per_usd: float | None,
    hhv_mj_per_nm3: float | None = None,
    params: Mapping[str, Param] | None = None,
) -> pd.DataFrame:
    """Place an LCOB inside the registry anchor ranges (docs/11 §8).

    The US$/MMBtu anchor needs ``brl_per_usd`` (no default: it is a dated scenario value) and a
    heating value (registry ``hhv_biomethane`` when ``hhv_mj_per_nm3`` is ``None``). With
    ``brl_per_usd=None`` that anchor is listed with ``engine_value`` and ``within_range`` empty.

    Returns:
        One row per anchor: ``anchor_id``, ``low``, ``central``, ``high``, ``unit``,
        ``engine_value`` (the LCOB in the anchor's unit), ``within_range``, ``confidence`` and
        ``note``.
    """
    p = params if params is not None else load_parameters()
    hhv = hhv_mj_per_nm3 if hhv_mj_per_nm3 is not None else p["hhv_biomethane"].require_central()
    rows = []
    for anchor_id, note in ANCHORS.items():
        a = p[anchor_id]
        if a.unit.startswith("US$ per MMBtu"):
            value = (
                None
                if brl_per_usd is None
                else brl_per_nm3_to_usd_per_mmbtu(
                    lcob_brl_per_nm3, hhv_mj_per_nm3=hhv, brl_per_usd=brl_per_usd
                )
            )
        elif a.unit.startswith("R$ per m3"):
            value = lcob_brl_per_nm3
        else:
            raise ValueError(f"{anchor_id}: unit {a.unit!r} is not handled")
        within = (
            None
            if value is None or a.low is None or a.high is None
            else bool(a.low <= value <= a.high)
        )
        rows.append(
            {
                "anchor_id": anchor_id,
                "low": a.low,
                "central": a.central,
                "high": a.high,
                "unit": a.unit,
                "engine_value": value,
                "within_range": within,
                "confidence": a.confidence,
                "note": note if value is not None else f"{note}; no exchange rate given",
            }
        )
    return pd.DataFrame(rows)
