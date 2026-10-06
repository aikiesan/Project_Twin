"""Level-1 CSTR mass balance with monthly operating constraints (docs/10 §2, v0).

For a plant with a monthly substrate mix this module computes CH₄, biogas and biomethane, the
digester loading (OLR, HRT), simple constraint flags and the capacity factor. It is the process
step of the walking skeleton (ADR-0010); ADM1 comes later (docs/10 §4).

Methane, per substrate *s* and month *t* (docs/10 §2.1):

- VS basis:  ``CH4 = m_fm · TS · VS/TS · BMP · f_scale · η_kin(HRT)``, with
  ``η_kin = 1 − exp(−k·HRT)`` when a first-order rate *k* is given (otherwise 1).
- COD basis (vinasse): ``CH4 = V · COD · η_COD · Y_CH4/COD``.

Biogas = CH₄ / x_CH4. Biomethane = CH₄ × methane recovery, capped at the upgrading nameplate
(the excess is reported as ``biomethane_curtailed_nm3``). Capacity factor = delivered biomethane
/ (nameplate × days in month).

Monthly checks (docs/10 §2.3): OLR ≤ max, HRT ≥ min, feed TS ≤ max (a conservative proxy for
digester TS), feed COD/SO₄ ≥ critical, feed K ≤ inhibition onset. Ammonia is **not evaluated**
in v0: the registry has no TAN content per substrate.

Units: gas volumes in Nm³ (0 °C, 1 atm); masses in t fresh matter (FM); volumes in m³; loads per
day. Every registry-built value records the parameter id it came from (:attr:`Substrate.param_ids`).
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Literal

import pandas as pd

from engine.registry import Param, load_parameters

#: Mass ratio K / K₂O (2·39.098 / 94.196), to turn the registry's K₂O into K.
K_PER_K2O = 2 * 39.098 / 94.196

#: Feed columns :func:`simulate` expects.
FEED_COLUMNS = ("month", "substrate", "fresh_t")


@dataclass(frozen=True)
class Substrate:
    """One feedstock, on a VS or a COD basis.

    Attributes:
        name: key used in the feed table.
        basis: ``"vs"`` (BMP per t VS) or ``"cod"`` (COD removal × CH₄ yield).
        density_t_per_m3: fresh-matter density, used for the hydraulic flow (HRT).
        ts_frac_fm: total solids, t TS per t FM.
        vs_frac_ts: volatile solids, t VS per t TS.
        bmp_nm3_ch4_per_t_vs: BMP (VS basis), Nm³ CH₄ per t VS (= NL per kg VS).
        k_first_order_per_d: first-order rate for η_kin; ``None`` means complete within HRT.
        cod_kg_per_m3, cod_removal_frac, ch4_yield_nm3_per_kg_cod: COD basis inputs.
        so4_kg_per_m3, k_kg_per_m3: for the COD/SO₄ and potassium checks (optional).
        ch4_frac_biogas: CH₄ fraction of the biogas this substrate yields (optional; used when
            :attr:`PlantDesign.x_ch4` is ``None``).
        param_ids: registry ids the values came from (empty for hand-made substrates).
    """

    name: str
    basis: Literal["vs", "cod"]
    density_t_per_m3: float
    ts_frac_fm: float
    vs_frac_ts: float
    bmp_nm3_ch4_per_t_vs: float | None = None
    k_first_order_per_d: float | None = None
    cod_kg_per_m3: float | None = None
    cod_removal_frac: float | None = None
    ch4_yield_nm3_per_kg_cod: float | None = None
    so4_kg_per_m3: float | None = None
    k_kg_per_m3: float | None = None
    ch4_frac_biogas: float | None = None
    param_ids: tuple[str, ...] = field(default=())

    def __post_init__(self) -> None:
        if self.basis not in ("vs", "cod"):
            raise ValueError(f"{self.name}: basis must be 'vs' or 'cod', not {self.basis!r}")
        if self.density_t_per_m3 <= 0:
            raise ValueError(f"{self.name}: density_t_per_m3 must be > 0")
        for attr in ("ts_frac_fm", "vs_frac_ts"):
            v = getattr(self, attr)
            if not 0 <= v <= 1:
                raise ValueError(f"{self.name}: {attr}={v} must be a fraction in [0, 1]")
        if self.ch4_frac_biogas is not None and not 0 < self.ch4_frac_biogas <= 1:
            raise ValueError(f"{self.name}: ch4_frac_biogas must be a fraction in (0, 1]")
        if self.basis == "vs" and self.bmp_nm3_ch4_per_t_vs is None:
            raise ValueError(f"{self.name}: VS basis needs bmp_nm3_ch4_per_t_vs")
        if self.basis == "cod":
            missing = [
                a
                for a in ("cod_kg_per_m3", "cod_removal_frac", "ch4_yield_nm3_per_kg_cod")
                if getattr(self, a) is None
            ]
            if missing:
                raise ValueError(f"{self.name}: COD basis needs {', '.join(missing)}")

    @property
    def vs_t_per_t_fm(self) -> float:
        """Volatile solids per tonne of fresh matter."""
        return self.ts_frac_fm * self.vs_frac_ts

    def ch4_nm3(self, fresh_t: float, hrt_d: float, bmp_fullscale: float) -> float:
        """CH₄ (Nm³) from ``fresh_t`` tonnes of this substrate at a given HRT (days)."""
        if fresh_t <= 0:
            return 0.0
        if self.basis == "cod":
            volume_m3 = fresh_t / self.density_t_per_m3
            return (
                volume_m3
                * self.cod_kg_per_m3  # type: ignore[operator]
                * self.cod_removal_frac
                * self.ch4_yield_nm3_per_kg_cod
            )
        eta = 1.0
        if self.k_first_order_per_d is not None:
            eta = 1.0 - math.exp(-self.k_first_order_per_d * hrt_d)
        return (
            fresh_t * self.vs_t_per_t_fm * self.bmp_nm3_ch4_per_t_vs * bmp_fullscale * eta
        )  # type: ignore[operator]


@dataclass(frozen=True)
class OperatingLimits:
    """Constraint thresholds (docs/10 §2.3) and the BMP→full-scale factor.

    ``ts_max_frac`` defaults to 0.12, the upper end of the wet-CSTR range in docs/10 §2.3
    (there is no registry row for it yet).
    """

    olr_max_kg_vs_m3_d: float
    hrt_min_d: float
    bmp_fullscale: float
    cod_so4_min: float | None = None
    k_max_kg_m3: float | None = None
    ts_max_frac: float = 0.12


@dataclass(frozen=True)
class PlantDesign:
    """Plant parameters for one simulation.

    Attributes:
        digester_volume_m3: total working volume.
        upgrading_capacity_nm3_d: nameplate biomethane output, Nm³/d.
        x_ch4: CH₄ fraction of the biogas for the whole mix, or ``None`` to derive it from each
            substrate's :attr:`Substrate.ch4_frac_biogas` (biogas = Σ CH₄_s / x_s).
        ch4_recovery_frac: upgrading CH₄ recovery (registry ``upg_ch4_recovery``).
    """

    digester_volume_m3: float
    upgrading_capacity_nm3_d: float
    x_ch4: float | None
    ch4_recovery_frac: float

    def __post_init__(self) -> None:
        if self.digester_volume_m3 <= 0 or self.upgrading_capacity_nm3_d <= 0:
            raise ValueError("digester_volume_m3 and upgrading_capacity_nm3_d must be > 0")
        if self.x_ch4 is not None and not 0 < self.x_ch4 <= 1:
            raise ValueError("x_ch4 must be a fraction in (0, 1] or None")
        if not 0 < self.ch4_recovery_frac <= 1:
            raise ValueError("ch4_recovery_frac must be a fraction in (0, 1]")


def _days_in_month(month: object) -> int:
    return pd.Period(str(month), freq="M").days_in_month


def _check_feed(feed: pd.DataFrame, substrates: Mapping[str, Substrate]) -> pd.DataFrame:
    missing = [c for c in FEED_COLUMNS if c not in feed.columns]
    if missing:
        raise ValueError(f"feed is missing column(s): {', '.join(missing)}")
    unknown = sorted(set(feed["substrate"]) - set(substrates))
    if unknown:
        raise KeyError(f"feed has substrate(s) with no definition: {', '.join(unknown)}")
    if (feed["fresh_t"] < 0).any():
        raise ValueError("fresh_t must be >= 0")
    return feed.groupby(["month", "substrate"], as_index=False, sort=True)["fresh_t"].sum()


def _monthly_loads(feed: pd.DataFrame, substrates: Mapping[str, Substrate]) -> pd.DataFrame:
    """Per month: days, fresh mass, flow (m³/d), VS load (kg/d), feed TS, COD/SO₄, feed K."""
    rows = []
    for month, grp in feed.groupby("month", sort=True):
        days = _days_in_month(month)
        fresh_t = vol_m3 = vs_t = ts_t = cod_kg = so4_kg = k_kg = 0.0
        cod_known = so4_known = k_known = True
        for sub_name, m in zip(grp["substrate"], grp["fresh_t"], strict=True):
            s = substrates[sub_name]
            v = m / s.density_t_per_m3
            fresh_t += m
            vol_m3 += v
            vs_t += m * s.vs_t_per_t_fm
            ts_t += m * s.ts_frac_fm
            if m > 0:
                cod_known &= s.cod_kg_per_m3 is not None
                so4_known &= s.so4_kg_per_m3 is not None
                k_known &= s.k_kg_per_m3 is not None
            cod_kg += v * (s.cod_kg_per_m3 or 0.0)
            so4_kg += v * (s.so4_kg_per_m3 or 0.0)
            k_kg += v * (s.k_kg_per_m3 or 0.0)
        rows.append(
            {
                "month": str(month),
                "days": days,
                "fresh_t": fresh_t,
                "flow_m3_d": vol_m3 / days,
                "vs_load_kg_d": vs_t * 1000 / days,
                "feed_ts_frac": ts_t / fresh_t if fresh_t else 0.0,
                "feed_cod_so4": (
                    cod_kg / so4_kg if cod_known and so4_known and so4_kg > 0 else math.nan
                ),
                "feed_k_kg_m3": k_kg / vol_m3 if k_known and vol_m3 > 0 else math.nan,
            }
        )
    return pd.DataFrame(rows)


def size_digester(
    feed: pd.DataFrame, substrates: Mapping[str, Substrate], limits: OperatingLimits
) -> float:
    """Smallest volume (m³) that meets OLR and HRT in every month (docs/10 §2.4)."""
    loads = _monthly_loads(_check_feed(feed, substrates), substrates)
    need = (loads["vs_load_kg_d"] / limits.olr_max_kg_vs_m3_d).combine(
        loads["flow_m3_d"] * limits.hrt_min_d, max
    )
    return float(need.max())


def simulate(
    feed: pd.DataFrame,
    substrates: Mapping[str, Substrate],
    design: PlantDesign,
    limits: OperatingLimits,
) -> pd.DataFrame:
    """Monthly mass balance and constraint flags.

    Args:
        feed: long table with :data:`FEED_COLUMNS` (``month`` like ``"2024-05"``, fresh tonnes
            per substrate and month). Months absent from the table are not simulated.
        substrates: definitions keyed by the names used in ``feed``.
        design: plant volume, nameplate and gas parameters.
        limits: constraint thresholds.

    Returns:
        One row per month: loads (``flow_m3_d``, ``vs_load_kg_d``, ``olr_kg_vs_m3_d``,
        ``hrt_d``), gas (``ch4_nm3``, ``biogas_nm3``, ``x_ch4_mix``, ``biomethane_potential_nm3``,
        ``biomethane_nm3``, ``biomethane_curtailed_nm3``, ``biomethane_nm3_d``),
        ``capacity_factor``, and flags ``olr_ok``, ``hrt_ok``, ``ts_ok``, ``cod_so4_ok``,
        ``k_ok`` (``None`` = not evaluable), ``tan_ok`` (always ``None`` in v0) and ``feasible``
        (all evaluable checks pass).
    """
    feed = _check_feed(feed, substrates)
    out = _monthly_loads(feed, substrates)
    v = design.digester_volume_m3
    out["olr_kg_vs_m3_d"] = out["vs_load_kg_d"] / v
    out["hrt_d"] = [v / q if q > 0 else math.inf for q in out["flow_m3_d"]]

    ch4, biogas = [], []
    for month, hrt in zip(out["month"], out["hrt_d"], strict=True):
        grp = feed[feed["month"].astype(str) == month]
        ch4_t = biogas_t = 0.0
        for name, m in zip(grp["substrate"], grp["fresh_t"], strict=True):
            s = substrates[name]
            c = s.ch4_nm3(m, hrt, limits.bmp_fullscale)
            ch4_t += c
            if design.x_ch4 is None and m > 0:
                if s.ch4_frac_biogas is None:
                    raise ValueError(
                        f"{name}: no ch4_frac_biogas; set PlantDesign.x_ch4 or the substrate "
                        "fraction (vinasse and filter cake: see docs/21 C13)"
                    )
                biogas_t += c / s.ch4_frac_biogas
        ch4.append(ch4_t)
        biogas.append(ch4_t / design.x_ch4 if design.x_ch4 is not None else biogas_t)
    out["ch4_nm3"] = ch4
    out["biogas_nm3"] = biogas
    out["x_ch4_mix"] = [c / b if b > 0 else math.nan for c, b in zip(ch4, biogas, strict=True)]
    out["biomethane_potential_nm3"] = out["ch4_nm3"] * design.ch4_recovery_frac
    nameplate_month = design.upgrading_capacity_nm3_d * out["days"]
    out["biomethane_nm3"] = out["biomethane_potential_nm3"].clip(upper=nameplate_month)
    out["biomethane_curtailed_nm3"] = out["biomethane_potential_nm3"] - out["biomethane_nm3"]
    out["biomethane_nm3_d"] = out["biomethane_nm3"] / out["days"]
    out["capacity_factor"] = out["biomethane_nm3"] / nameplate_month

    out["olr_ok"] = out["olr_kg_vs_m3_d"] <= limits.olr_max_kg_vs_m3_d
    out["hrt_ok"] = out["hrt_d"] >= limits.hrt_min_d
    out["ts_ok"] = out["feed_ts_frac"] <= limits.ts_max_frac
    # object dtype keeps the three states True / False / None (not evaluable) as Python values
    out["cod_so4_ok"] = pd.Series(
        [
            None if limits.cod_so4_min is None or math.isnan(r) else bool(r >= limits.cod_so4_min)
            for r in out["feed_cod_so4"]
        ],
        dtype=object,
    )
    out["k_ok"] = pd.Series(
        [
            None if limits.k_max_kg_m3 is None or math.isnan(k) else bool(k <= limits.k_max_kg_m3)
            for k in out["feed_k_kg_m3"]
        ],
        dtype=object,
    )
    out["tan_ok"] = pd.Series([None] * len(out), dtype=object)
    checks = ["olr_ok", "hrt_ok", "ts_ok", "cod_so4_ok", "k_ok"]
    out["feasible"] = [
        all(bool(row[c]) for c in checks if row[c] is not None) for _, row in out.iterrows()
    ]
    return out


# --- registry builders ------------------------------------------------------------------------


def _split_pair(p: Param) -> tuple[float, float]:
    """Parse a registry ``"a / b"`` central value (e.g. TS / VS)."""
    try:
        a, b = (float(x) for x in p.raw_central.split("/"))
    except ValueError as exc:
        raise ValueError(f"{p.id}: expected 'a / b' in central, got {p.raw_central!r}") from exc
    return a, b


def _central(params: Mapping[str, Param], pid: str) -> float:
    return params[pid].require_central()


#: VS-basis substrates built from four registry rows each: ``<prefix>_ts`` (% FM),
#: ``<prefix>_vs_ts`` (% TS), a BMP row (NL CH₄/kg VS) and ``<prefix>_ch4_pct`` (% v/v).
VS_SUBSTRATE_ROWS = {
    "straw": ("straw", "straw_bmp_untreated"),
    "cattle_slurry": ("cattle_slurry", "cattle_slurry_bmp"),
    "swine_slurry": ("swine_slurry", "swine_slurry_bmp"),
    "poultry_droppings": ("poultry_droppings", "poultry_droppings_bmp"),
    "poultry_litter": ("poultry_litter", "poultry_litter_bmp"),
}


def _vs_substrate(
    p: Mapping[str, Param], name: str, prefix: str, bmp_id: str, density: float
) -> Substrate:
    ids = (f"{prefix}_ts", f"{prefix}_vs_ts", bmp_id, f"{prefix}_ch4_pct")
    return Substrate(
        name=name,
        basis="vs",
        density_t_per_m3=density,
        ts_frac_fm=_central(p, ids[0]) / 100,
        vs_frac_ts=_central(p, ids[1]) / 100,
        bmp_nm3_ch4_per_t_vs=_central(p, bmp_id),  # NL/kg VS = Nm³/t VS
        ch4_frac_biogas=_central(p, ids[3]) / 100,
        param_ids=ids,
    )


def substrates_from_registry(
    params: Mapping[str, Param] | None = None, *, fresh_density_t_per_m3: float = 1.0
) -> dict[str, Substrate]:
    """All v0 substrates from ``parameters.csv`` central values.

    - vinasse (COD basis) and filter cake (VS basis): no ``ch4_frac_biogas`` yet, because the
      CH₄ fraction of vinasse is in conflict (docs/21 C13) and filter cake has no row;
    - straw and four manures (VS basis) from :data:`VS_SUBSTRATE_ROWS`, with their CH₄ fraction.

    ``fresh_density_t_per_m3`` converts fresh mass to volume for the HRT. The registry has no
    density row; 1.0 t/m³ is a v0 modelling assumption (docs/10 §7), passed explicitly here so
    it shows in every call that relies on it.
    """
    p = params if params is not None else load_parameters()
    vin_ts_g_l, vin_vs_g_l = _split_pair(p["vin_ts_vs"])
    fc_ts_pct, fc_vs_pct_ts = _split_pair(p["fc_ts_vs"])
    vinasse = Substrate(
        name="vinasse",
        basis="cod",
        density_t_per_m3=fresh_density_t_per_m3,
        ts_frac_fm=vin_ts_g_l / 1000 / fresh_density_t_per_m3,
        vs_frac_ts=vin_vs_g_l / vin_ts_g_l,
        cod_kg_per_m3=_central(p, "vin_cod"),  # g/L = kg/m³
        cod_removal_frac=_central(p, "cod_removal") / 100,
        ch4_yield_nm3_per_kg_cod=_central(p, "vin_ch4_yield"),
        so4_kg_per_m3=_central(p, "vin_so4"),
        k_kg_per_m3=_central(p, "vin_k2o") * K_PER_K2O,
        param_ids=(
            "vin_ts_vs",
            "vin_cod",
            "cod_removal",
            "vin_ch4_yield",
            "vin_so4",
            "vin_k2o",
        ),
    )
    filter_cake = Substrate(
        name="filter_cake",
        basis="vs",
        density_t_per_m3=fresh_density_t_per_m3,
        ts_frac_fm=fc_ts_pct / 100,
        vs_frac_ts=fc_vs_pct_ts / 100,
        bmp_nm3_ch4_per_t_vs=_central(p, "fc_bmp"),  # NL/kg VS = Nm³/t VS
        param_ids=("fc_ts_vs", "fc_bmp"),
    )
    built = {"vinasse": vinasse, "filter_cake": filter_cake}
    for name, (prefix, bmp_id) in VS_SUBSTRATE_ROWS.items():
        built[name] = _vs_substrate(p, name, prefix, bmp_id, fresh_density_t_per_m3)
    return built


def limits_from_registry(params: Mapping[str, Param] | None = None) -> OperatingLimits:
    """Constraint thresholds from ``parameters.csv`` central values."""
    p = params if params is not None else load_parameters()
    return OperatingLimits(
        olr_max_kg_vs_m3_d=_central(p, "olr_max_cstr"),
        hrt_min_d=p["hrt_cstr"].low if p["hrt_cstr"].low is not None else _central(p, "hrt_cstr"),
        bmp_fullscale=_central(p, "bmp_fullscale"),
        cod_so4_min=_central(p, "cod_so4_crit"),
        k_max_kg_m3=_central(p, "k_inhib"),  # g K/L = kg/m³
    )


#: Inputs the v0 skeleton needs that the registry does not hold yet (docs/10 §7).
REGISTRY_GAPS = {
    "x_ch4_vinasse_filter_cake": "CH4 fraction of biogas for vinasse (in conflict, docs/21 C13) "
    "and filter cake (no registry row)",
    "fresh_density": "fresh-matter density per substrate (v0 assumes 1.0 t/m3)",
    "tan_content": "TAN per substrate, for the ammonia check",
}
