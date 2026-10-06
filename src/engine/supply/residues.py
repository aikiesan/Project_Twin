"""Residues v0: cane crushed per mill → monthly vinasse, filter cake and straw (docs/09 Step 4–5).

This is the supply step of the walking skeleton (ADR-0010). For one mill and one crop year it
turns the cane crushed in the season into monthly residue streams and then into the feed table
that :func:`engine.process.mass_balance.simulate` reads.

Per crop year (registry ids in brackets):

- ethanol (L) = cane (t) × ethanol yield (L/t) [``ethanol_yield``], unless the mill's own
  ethanol volume is given (for example from its RenovaBio report);
- vinasse **generated** (m³) = ethanol (L) × vinasse ratio (L/L) [``vin_gen``] / 1000;
- filter cake **generated** (t FM) = cane (t) × generation (kg/t) [``fc_gen``] / 1000;
- straw **recoverable** (t DM) = cane (t) × straw (kg DM/t) [``straw_gen``] × recoverable
  fraction [``straw_recov``] / 1000; fresh mass = DM / TS [``straw_ts``].

The streams are spread over the months with a harvest profile (share of the season's crush per
calendar month). Until the UNICA biweekly series is in, :data:`UNIFORM_APR_NOV` is used: equal
shares from April to November. It is a v0 modelling assumption, not a measured profile.

**Generated ≠ available for AD** (CLAUDE.md §2 rule 9). The share of each stream that goes to
the digester is an explicit argument with no default (``*_to_ad_frac``); it is a calibration
target (docs/13 §3.2, "effective feedstock share delivered"). Vinasse that passes through the
digester is still applied in fertirrigation as digestate, so AD does not compete with it.

Units: cane and fresh/dry masses in t; liquid volumes in m³; one row per calendar month of the
crop year (April of ``crop_year`` to March of the next year), with zeros outside the harvest.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field

import pandas as pd

from engine.registry import Param, load_parameters

#: v0 harvest profile: equal shares April–November (month number → share of the season's crush).
#: A modelling assumption until the UNICA biweekly series is downloaded (docs/19 Phase 0).
UNIFORM_APR_NOV: dict[int, float] = {m: 1 / 8 for m in range(4, 12)}

#: Calendar months of a crop year, in order, starting in April (docs/09 Step 5).
CROP_YEAR_MONTHS = (4, 5, 6, 7, 8, 9, 10, 11, 12, 1, 2, 3)

#: Substrate names in the feed table; they match :func:`substrates_from_registry`.
FEED_SUBSTRATES = ("vinasse", "filter_cake", "straw")


@dataclass(frozen=True)
class ResidueCoefficients:
    """Generation coefficients for one mill.

    Attributes:
        ethanol_l_per_t_cane: ethanol yield, L per t cane.
        vinasse_l_per_l_ethanol: vinasse generated, L per L ethanol.
        filter_cake_kg_per_t_cane: filter cake generated, kg fresh matter per t cane.
        straw_kg_dm_per_t_cane: straw produced in the field, kg dry matter per t cane.
        straw_recoverable_frac: share of the straw that can be removed from the field.
        straw_ts_frac_fm: total solids of recovered straw, t DM per t fresh matter.
        param_ids: registry ids the values came from (empty for hand-made coefficients).
    """

    ethanol_l_per_t_cane: float
    vinasse_l_per_l_ethanol: float
    filter_cake_kg_per_t_cane: float
    straw_kg_dm_per_t_cane: float
    straw_recoverable_frac: float
    straw_ts_frac_fm: float
    param_ids: tuple[str, ...] = field(default=())

    def __post_init__(self) -> None:
        for attr in (
            "ethanol_l_per_t_cane",
            "vinasse_l_per_l_ethanol",
            "filter_cake_kg_per_t_cane",
            "straw_kg_dm_per_t_cane",
        ):
            if getattr(self, attr) < 0:
                raise ValueError(f"{attr} must be >= 0")
        if not 0 <= self.straw_recoverable_frac <= 1:
            raise ValueError("straw_recoverable_frac must be a fraction in [0, 1]")
        if not 0 < self.straw_ts_frac_fm <= 1:
            raise ValueError("straw_ts_frac_fm must be a fraction in (0, 1]")


def coefficients_from_registry(params: Mapping[str, Param] | None = None) -> ResidueCoefficients:
    """Residue coefficients from ``parameters.csv`` central values, with their ids."""
    p = params if params is not None else load_parameters()
    ids = ("ethanol_yield", "vin_gen", "fc_gen", "straw_gen", "straw_recov", "straw_ts")
    return ResidueCoefficients(
        ethanol_l_per_t_cane=p["ethanol_yield"].require_central(),
        vinasse_l_per_l_ethanol=p["vin_gen"].require_central(),
        filter_cake_kg_per_t_cane=p["fc_gen"].require_central(),
        straw_kg_dm_per_t_cane=p["straw_gen"].require_central(),
        straw_recoverable_frac=p["straw_recov"].require_central(),
        straw_ts_frac_fm=p["straw_ts"].require_central() / 100,  # % FM -> fraction
        param_ids=ids,
    )


def check_profile(profile: Mapping[int, float]) -> dict[int, float]:
    """Validate a harvest profile: calendar months 1–12, shares >= 0 that sum to 1."""
    bad = sorted(m for m in profile if m not in range(1, 13))
    if bad:
        raise ValueError(f"profile months must be 1-12, got {bad}")
    if any(v < 0 for v in profile.values()):
        raise ValueError("profile shares must be >= 0")
    total = sum(profile.values())
    if not math.isclose(total, 1.0, abs_tol=1e-9):
        raise ValueError(f"profile shares must sum to 1, got {total}")
    return {m: float(profile.get(m, 0.0)) for m in range(1, 13)}


def _fraction(name: str, value: float) -> float:
    if not 0 <= value <= 1:
        raise ValueError(f"{name} must be a fraction in [0, 1], got {value}")
    return value


def monthly_residues(
    cane_t: float,
    crop_year: int,
    coeffs: ResidueCoefficients,
    *,
    vinasse_to_ad_frac: float,
    filter_cake_to_ad_frac: float,
    straw_to_ad_frac: float,
    profile: Mapping[int, float] = UNIFORM_APR_NOV,
    ethanol_l: float | None = None,
) -> pd.DataFrame:
    """Monthly residue streams for one mill and one crop year.

    Args:
        cane_t: cane crushed in the season, t.
        crop_year: year in which the season starts (April); rows run from April of this year to
            March of the next.
        coeffs: generation coefficients (see :func:`coefficients_from_registry`).
        vinasse_to_ad_frac, filter_cake_to_ad_frac, straw_to_ad_frac: share of each generated
            (straw: recoverable) stream sent to the digester. No defaults: they are calibration
            targets, not registry parameters.
        profile: share of the season's crush per calendar month (see :func:`check_profile`).
        ethanol_l: the mill's own ethanol volume for the season, L. When given, it replaces
            ``cane_t × ethanol_l_per_t_cane`` (for example from a RenovaBio report).

    Returns:
        One row per month (``month`` as ``"YYYY-MM"``) with ``cane_t``, ``ethanol_m3``,
        ``vinasse_generated_m3``, ``vinasse_to_ad_m3``, ``filter_cake_generated_t_fm``,
        ``filter_cake_to_ad_t_fm``, ``straw_recoverable_t_dm``, ``straw_to_ad_t_fm``.
    """
    if cane_t < 0:
        raise ValueError("cane_t must be >= 0")
    if ethanol_l is not None and ethanol_l < 0:
        raise ValueError("ethanol_l must be >= 0")
    shares = check_profile(profile)
    f_vin = _fraction("vinasse_to_ad_frac", vinasse_to_ad_frac)
    f_fc = _fraction("filter_cake_to_ad_frac", filter_cake_to_ad_frac)
    f_straw = _fraction("straw_to_ad_frac", straw_to_ad_frac)

    ethanol_season_l = cane_t * coeffs.ethanol_l_per_t_cane if ethanol_l is None else ethanol_l
    rows = []
    for m in CROP_YEAR_MONTHS:
        year = crop_year if m >= 4 else crop_year + 1
        s = shares[m]
        cane = cane_t * s
        ethanol_m3 = ethanol_season_l * s / 1000
        vinasse_m3 = ethanol_m3 * coeffs.vinasse_l_per_l_ethanol
        cake_t = cane * coeffs.filter_cake_kg_per_t_cane / 1000
        straw_dm_t = cane * coeffs.straw_kg_dm_per_t_cane * coeffs.straw_recoverable_frac / 1000
        rows.append(
            {
                "month": f"{year:04d}-{m:02d}",
                "cane_t": cane,
                "ethanol_m3": ethanol_m3,
                "vinasse_generated_m3": vinasse_m3,
                "vinasse_to_ad_m3": vinasse_m3 * f_vin,
                "filter_cake_generated_t_fm": cake_t,
                "filter_cake_to_ad_t_fm": cake_t * f_fc,
                "straw_recoverable_t_dm": straw_dm_t,
                "straw_to_ad_t_fm": straw_dm_t * f_straw / coeffs.straw_ts_frac_fm,
            }
        )
    return pd.DataFrame(rows)


def to_feed(residues: pd.DataFrame, *, vinasse_density_t_per_m3: float) -> pd.DataFrame:
    """Long feed table (``month``, ``substrate``, ``fresh_t``) for the process module.

    ``vinasse_density_t_per_m3`` turns the vinasse volume into the fresh mass that
    :func:`engine.process.mass_balance.simulate` expects. Use the same density as the vinasse
    :class:`~engine.process.mass_balance.Substrate`, so the volume round-trips exactly (the
    registry has no density row; docs/10 §7).
    """
    if vinasse_density_t_per_m3 <= 0:
        raise ValueError("vinasse_density_t_per_m3 must be > 0")
    cols = {
        "vinasse": residues["vinasse_to_ad_m3"] * vinasse_density_t_per_m3,
        "filter_cake": residues["filter_cake_to_ad_t_fm"],
        "straw": residues["straw_to_ad_t_fm"],
    }
    parts = [
        pd.DataFrame({"month": residues["month"], "substrate": name, "fresh_t": values})
        for name, values in cols.items()
    ]
    return pd.concat(parts, ignore_index=True)
