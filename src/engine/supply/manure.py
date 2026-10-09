"""Manure base-load v0: PPM herds → manure → volatile solids → CH₄ potential (docs/09 §Manure).

For one species, municipality and year (registry ids in brackets):

- manure (t FM/yr) = head × manure rate per head per day × 365 / 1000, where a rate given in
  L per head per day is turned into kg with the slurry density;
- VS (t/yr) = manure (t FM) × TS (% FM) / 100 × VS (% TS) / 100;
- CH₄ **theoretical** (Nm³/yr) = VS (t) × BMP (NL CH₄ per kg VS = Nm³ per t VS);
- CH₄ **collectable** (Nm³/yr) = theoretical × collectable fraction.

What the numbers are, and are not:

- *Theoretical* counts the manure of **every head** in the PPM herd. In SP most cattle graze, so
  their manure cannot be collected; the collectable (confined) share is the decisive input. It is
  an explicit argument with no default (``collect_frac``): the registry has no sourced value yet
  (docs/21 Q-manure). Rows without it report ``ch4_nm3_yr_collectable`` as missing.
- BMP is a laboratory maximum, not plant output; process conversion comes later (docs/10).
- Biogas ≠ CH₄ ≠ biomethane (CLAUDE.md §2 rule 10): every output here is CH₄ volume, Nm³ at 0 °C.

Species are configured in :data:`SPECIES`. A species is computed only when every coefficient it
needs is in the registry with a numeric central value; otherwise it is listed by
:func:`missing_coefficients` and skipped, never filled with a guessed number.

Input: the long municipal time series of PILAR-2b (``municipality_timeseries``, source
``ibge_ppm``): columns ``ibge_code``, ``year``, ``variable``, ``value``, ``unit`` (unit ``head``).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

import pandas as pd

from engine.registry import Param, load_parameters

DAYS_PER_YEAR = 365


@dataclass(frozen=True)
class SpeciesSpec:
    """Which PPM variable and which registry ids describe one manure stream.

    Attributes:
        species: name used in the output (e.g. ``"swine"``).
        ppm_variable: herd variable in the PPM long table (unit ``head``).
        rate_param: manure generated per head per day.
        rate_basis: ``"L"`` (litres, needs ``density_param``) or ``"kg"`` (fresh matter).
        ts_param, vs_ts_param, bmp_param: registry ids for TS (% FM), VS (% TS) and BMP
            (NL CH₄ per kg VS).
        density_param: slurry density in t/m³ (= kg/L); only for ``rate_basis="L"``.
        note: what the herd count covers and why that matters.
    """

    species: str
    ppm_variable: str
    rate_param: str
    rate_basis: str
    ts_param: str
    vs_ts_param: str
    bmp_param: str
    density_param: str | None = None
    note: str = ""

    def param_ids(self) -> tuple[str, ...]:
        ids = (self.rate_param, self.ts_param, self.vs_ts_param, self.bmp_param)
        return ids + ((self.density_param,) if self.density_param else ())


#: v0 species. Rates are per head of the PPM herd variable named; see each note.
SPECIES: tuple[SpeciesSpec, ...] = (
    SpeciesSpec(
        species="swine",
        ppm_variable="suino_total",
        rate_param="swine_manure",
        rate_basis="L",
        density_param="swine_slurry_density",
        ts_param="swine_slurry_ts",
        vs_ts_param="swine_slurry_vs_ts",
        bmp_param="swine_slurry_bmp",
        note="Finishing-pig slurry rate applied to the whole herd (sows and piglets included).",
    ),
    SpeciesSpec(
        species="poultry",
        ppm_variable="galinaceos_total",
        rate_param="poultry_droppings_gen",
        rate_basis="kg",
        ts_param="poultry_droppings_ts",
        vs_ts_param="poultry_droppings_vs_ts",
        bmp_param="poultry_droppings_bmp",
        note="Layers and broilers together; needs a per-bird droppings rate (not in the registry).",
    ),
    SpeciesSpec(
        species="cattle",
        ppm_variable="bovino",
        rate_param="cattle_manure_per_head",
        rate_basis="kg",
        ts_param="cattle_slurry_ts",
        vs_ts_param="cattle_slurry_vs_ts",
        bmp_param="cattle_slurry_bmp",
        note="Whole herd, mostly grazing in SP; needs a herd-average rate (dairy_manure is per "
        "milked cow, feedlot_manure per confined head, and PPM 3939 counts neither).",
    ),
)


def missing_coefficients(
    params: Mapping[str, Param] | None = None, species: tuple[SpeciesSpec, ...] = SPECIES
) -> dict[str, list[str]]:
    """Registry ids each species still lacks (absent, or no numeric central value)."""
    p = params if params is not None else load_parameters()
    out: dict[str, list[str]] = {}
    for s in species:
        lack = [i for i in s.param_ids() if i not in p or p[i].central is None]
        if lack:
            out[s.species] = lack
    return out


def _vs_t_per_head_yr(s: SpeciesSpec, p: Mapping[str, Param]) -> tuple[float, float]:
    """(manure t FM per head per year, VS t per head per year) for one species."""
    rate = p[s.rate_param].require_central()
    if s.rate_basis == "L":
        if not s.density_param:
            raise ValueError(f"{s.species}: a rate in litres needs density_param")
        kg_per_day = rate * p[s.density_param].require_central()  # L/d × kg/L
    elif s.rate_basis == "kg":
        kg_per_day = rate
    else:
        raise ValueError(f"{s.species}: rate_basis must be 'L' or 'kg', got {s.rate_basis!r}")
    fm_t = kg_per_day * DAYS_PER_YEAR / 1000
    ts = p[s.ts_param].require_central() / 100
    vs_ts = p[s.vs_ts_param].require_central() / 100
    return fm_t, fm_t * ts * vs_ts


def manure_potential(
    herds: pd.DataFrame,
    *,
    collect_frac: Mapping[str, float] | None = None,
    params: Mapping[str, Param] | None = None,
    species: tuple[SpeciesSpec, ...] = SPECIES,
) -> pd.DataFrame:
    """CH₄ potential of manure per municipality, year and species.

    Args:
        herds: long PPM table with ``ibge_code``, ``year``, ``variable``, ``value`` and ``unit``.
        collect_frac: collectable (confined) share per species, in [0, 1]. Species left out get
            a missing ``ch4_nm3_yr_collectable``.
        params: registry parameters (defaults to ``parameters.csv``).
        species: species to compute; those with missing coefficients are skipped.

    Returns:
        One row per ``ibge_code``, ``year``, ``species`` with ``head``, ``manure_t_fm_yr``,
        ``vs_t_yr``, ``ch4_nm3_yr_theoretical``, ``collect_frac``, ``ch4_nm3_yr_collectable``
        and ``param_ids``.
    """
    p = params if params is not None else load_parameters()
    collect_frac = dict(collect_frac or {})
    for name, f in collect_frac.items():
        if not 0 <= f <= 1:
            raise ValueError(f"collect_frac[{name!r}] must be a fraction in [0, 1], got {f}")
    need = {"ibge_code", "year", "variable", "value", "unit"}
    if lacking := need - set(herds.columns):
        raise ValueError(f"herds is missing columns {sorted(lacking)}")

    missing = missing_coefficients(p, species)
    frames = []
    for s in species:
        if s.species in missing:
            continue
        h = herds[herds["variable"] == s.ppm_variable]
        bad_units = set(h["unit"]) - {"head"}
        if bad_units:
            raise ValueError(f"{s.ppm_variable}: expected unit 'head', got {sorted(bad_units)}")
        fm_t, vs_t = _vs_t_per_head_yr(s, p)
        bmp = p[s.bmp_param].require_central()  # NL/kg VS = Nm3/t VS
        f = collect_frac.get(s.species)
        out = pd.DataFrame(
            {
                "ibge_code": h["ibge_code"].astype(str).to_numpy(),
                "year": h["year"].astype(int).to_numpy(),
                "species": s.species,
                "head": h["value"].astype(float).to_numpy(),
            }
        )
        out["manure_t_fm_yr"] = out["head"] * fm_t
        out["vs_t_yr"] = out["head"] * vs_t
        out["ch4_nm3_yr_theoretical"] = out["vs_t_yr"] * bmp
        out["collect_frac"] = f
        out["ch4_nm3_yr_collectable"] = (
            out["ch4_nm3_yr_theoretical"] * f if f is not None else float("nan")
        )
        out["param_ids"] = ";".join(s.param_ids())
        frames.append(out)
    cols = [
        "ibge_code",
        "year",
        "species",
        "head",
        "manure_t_fm_yr",
        "vs_t_yr",
        "ch4_nm3_yr_theoretical",
        "collect_frac",
        "ch4_nm3_yr_collectable",
        "param_ids",
    ]
    if not frames:
        return pd.DataFrame(columns=cols)
    return pd.concat(frames, ignore_index=True)[cols].sort_values(
        ["ibge_code", "year", "species"], ignore_index=True
    )
