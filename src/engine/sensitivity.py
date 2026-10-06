"""Morris screening of the walking skeleton: which registry rows to verify first (ADR-0010).

The screen ranks the registry rows the skeleton reads (:func:`engine.skeleton.run_chain`) by
how much they move four outputs of one crop year:

- ``annual_biomethane_nm3`` — delivered biomethane, Nm³;
- ``capacity_factor_annual`` — delivered / (nameplate × days);
- ``lcob_brl_per_nm3`` — annuity LCOB, R$ per Nm³ (price year of the CAPEX row);
- ``months_infeasible`` — months that fail a mass-balance check (docs/10 §2.3).

The ranking decides the order of page-level verification (flag ``V``, docs/08 §5): rows that
move the results first, rows with no effect last. It is a screen, not an uncertainty analysis.

**Factors.** One factor per registry row, because one row is one source and one verification
task (ADR-0013):

- a row with numeric ``central``, ``low`` and ``high`` and ``low < high`` is screened over
  ``[low, high]``;
- a pair row (central ``"a / b"``, low ``"a1-a2 / b1-b2"``, e.g. ``fc_ts_vs``) is one factor:
  both components move to the same quantile of their own ranges;
- every other row is **excluded** and listed with its reason (no range, ``low = high``,
  non-numeric). Nothing is dropped silently.

A factor value *v* replaces the row by ``central = low = high = v``, so code that reads the low
end (``hrt_cstr`` is used as a minimum HRT) sees the same value.

**Method.** Elementary effects (Morris 1991) summarised by μ* (Campolongo et al. 2007), via
SALib (Herman and Usher 2017). Each factor is sampled on a ``levels``-point grid of its quantile
``q ∈ [0, 1]``, mapped to ``low + q · (high − low)``. Uniform over the registry range is a
screening choice, not a claim about the distribution of the value. μ* is reported in output
units and relative to the central-case output (``mu_star_rel``).

**Local elasticities.** Every row with a numeric central value, screened or not, also gets
``ε = (y(x(1+δ)) − y(x(1−δ))) / (2 δ · y(x))``. Rows without a range are therefore not ignored:
a large ε says that a sourced range is worth finding.

**Reference case.** Either a calibration mill from ``registry/skeleton_mills.yaml`` (same inputs
and ANP nameplate as :func:`engine.skeleton.run_skeleton`) or a labelled **synthetic** case:
a cane normalisation unit, the mills' AD shares, and the nameplate sized to the peak month of
the central-value potential. With linear CAPEX the synthetic LCOB, capacity factor and
``mu_star_rel`` do not depend on the cane value; only the biomethane volume scales with it. The
synthetic case is not a mill and its numbers are not results (ADR-0010).

Usage::

    python -m engine.sensitivity morris --synthetic
    python -m engine.sensitivity morris --mill costa_pinto --crop-year 2025
"""

from __future__ import annotations

import argparse
import json
import math
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path

import numpy as np
import pandas as pd

from engine import DATA_DIR, __version__
from engine.process.strategies import StorageS1
from engine.registry import Param, load_parameters, param_hash
from engine.skeleton import (
    ANP_MONTHLY_CSV,
    SKELETON_MILLS_YAML,
    MissingInputError,
    _git_commit,
    load_anp_monthly,
    load_mill_configs,
    missing_inputs,
    nameplate_from_anp,
    run_chain,
    storage_from_config,
)

DEFAULT_OUT_DIR = DATA_DIR / "processed" / "sensitivity"

#: Outputs of one chain evaluation, in report order.
OUTPUTS = (
    "annual_biomethane_nm3",
    "capacity_factor_annual",
    "lcob_brl_per_nm3",
    "months_infeasible",
)

#: Outputs that set the verification priority (``months_infeasible`` is a count, often 0 in the
#: central case, so it is reported but not used to rank).
PRIORITY_OUTPUTS = ("annual_biomethane_nm3", "capacity_factor_annual", "lcob_brl_per_nm3")

#: Size of the top list for the Gate 0 metric (docs/19: ≥ 60 % of the top 15 are ``V``).
GATE0_TOP_N = 15

#: AD shares of the synthetic case: those of both calibration mills in skeleton_mills.yaml.
SYNTHETIC_AD_SHARES = {"vinasse": 1.0, "filter_cake": 1.0, "straw": 0.0}

#: Cane normalisation unit of the synthetic case, t (a unit, not a mill's crush).
SYNTHETIC_CANE_T = 1_000_000.0

#: Inputs the chain uses that are not registry rows, so the screen does not cover them.
NOT_SCREENED = {
    "cane_t": "scale input; the synthetic case's relative results do not depend on it",
    "ad_shares": "calibration start values (skeleton_mills.yaml), tuned against ANP later",
    "x_ch4": "changes biogas only, not CH4, biomethane or LCOB (docs/21 C13 matters for the "
    "ANP biogas comparison)",
    "nameplate": "design input: ANP capacity (mill case) or central-case peak (synthetic case)",
    "harvest_profile": "fixed uniform April-November profile (docs/09 §5) until UNICA biweekly",
    "fresh_density": "1.0 t/m3 modelling assumption, no registry row (docs/10 §7)",
    "ts_max_frac": "OperatingLimits default, no registry row (docs/10 §2.3)",
    "storage": "S1 scenario inputs (store_frac, loss per month), not registry rows",
}

_RANGE_PAIR_RE = re.compile(
    r"^\s*([\d.]+)\s*-\s*([\d.]+)\s*/\s*([\d.]+)\s*-\s*([\d.]+)\s*$"
)  # "a1-a2 / b1-b2"
_CENTRAL_PAIR_RE = re.compile(r"^\s*([\d.]+)\s*/\s*([\d.]+)\s*$")  # "a / b"


@dataclass(frozen=True)
class Factor:
    """One screened registry row.

    Attributes:
        pid: parameter id.
        lows, highs, centrals: one entry per component (one for a scalar row, two for a pair).
        unit, confidence, source: copied from the registry row.
    """

    pid: str
    lows: tuple[float, ...]
    highs: tuple[float, ...]
    centrals: tuple[float, ...]
    unit: str
    confidence: str
    source: str

    @property
    def is_pair(self) -> bool:
        return len(self.centrals) == 2

    def value_at(self, q: float) -> tuple[float, ...]:
        """Component values at quantile ``q`` of the range (0 = low, 1 = high)."""
        return tuple(lo + q * (hi - lo) for lo, hi in zip(self.lows, self.highs, strict=True))


@dataclass(frozen=True)
class Excluded:
    """A registry row the chain reads but the Morris screen does not vary."""

    pid: str
    reason: str
    confidence: str
    source: str


def _factor_or_reason(p: Param) -> Factor | str:
    if _CENTRAL_PAIR_RE.match(p.raw_central):
        m = _RANGE_PAIR_RE.match(p.raw_low)
        if not m:
            return f"pair row without an 'a1-a2 / b1-b2' range (low={p.raw_low!r})"
        a1, a2, b1, b2 = (float(x) for x in m.groups())
        c = _CENTRAL_PAIR_RE.match(p.raw_central)
        assert c is not None
        if a1 >= a2 or b1 >= b2:
            return f"pair range not increasing (low={p.raw_low!r})"
        return Factor(
            pid=p.id,
            lows=(a1, b1),
            highs=(a2, b2),
            centrals=(float(c.group(1)), float(c.group(2))),
            unit=p.unit,
            confidence=p.confidence,
            source=p.source,
        )
    if p.central is None:
        return f"non-numeric central value ({p.raw_central!r})"
    if not p.has_range:
        return "no numeric range in the registry"
    assert p.low is not None and p.high is not None
    if p.low >= p.high:
        return f"low ({p.raw_low}) is not below high ({p.raw_high})"
    return Factor(
        pid=p.id,
        lows=(p.low,),
        highs=(p.high,),
        centrals=(p.central,),
        unit=p.unit,
        confidence=p.confidence,
        source=p.source,
    )


def factor_space(
    params: Mapping[str, Param], param_ids: Sequence[str]
) -> tuple[list[Factor], list[Excluded]]:
    """Split the chain's registry rows into screened factors and excluded rows (with reasons)."""
    factors, excluded = [], []
    for pid in param_ids:
        got = _factor_or_reason(params[pid])
        if isinstance(got, Factor):
            factors.append(got)
        else:
            p = params[pid]
            excluded.append(Excluded(pid, got, p.confidence, p.source))
    return factors, excluded


def _fmt_num(x: float) -> str:
    return repr(float(x))


def set_row(params: Mapping[str, Param], pid: str, values: Sequence[float]) -> dict[str, Param]:
    """Copy of ``params`` with row ``pid`` set to ``values`` (``central = low = high``).

    One value for a scalar row, two for a pair row (``"a / b"``).
    """
    p = params[pid]
    if len(values) == 1:
        v = float(values[0])
        new = replace(
            p,
            central=v,
            low=v,
            high=v,
            raw_central=_fmt_num(v),
            raw_low=_fmt_num(v),
            raw_high=_fmt_num(v),
        )
    elif len(values) == 2:
        text = f"{_fmt_num(values[0])} / {_fmt_num(values[1])}"
        new = replace(p, central=None, low=None, high=None, raw_central=text, raw_low=text)
    else:
        raise ValueError(f"{pid}: expected 1 or 2 values, got {len(values)}")
    out = dict(params)
    out[pid] = new
    return out


@dataclass(frozen=True)
class ReferenceCase:
    """Inputs of the chain that the screen holds fixed.

    Attributes:
        label: ``synthetic`` or ``<mill>-<crop year>``.
        basis: where the inputs come from (shown in every output).
        cane_t, crop_year, ad_shares, x_ch4, nameplate_biomethane_nm3_d, storage, ethanol_l:
            as in :func:`engine.skeleton.run_chain`.
    """

    label: str
    basis: str
    cane_t: float
    crop_year: int
    ad_shares: Mapping[str, float]
    x_ch4: float
    nameplate_biomethane_nm3_d: float
    storage: StorageS1 | None = None
    ethanol_l: float | None = None

    def to_dict(self) -> dict:
        d = asdict(self)
        d["ad_shares"] = dict(self.ad_shares)
        return d


def synthetic_case(
    params: Mapping[str, Param] | None = None,
    *,
    cane_t: float = SYNTHETIC_CANE_T,
    crop_year: int = 2025,
    x_ch4: float = 0.575,
) -> ReferenceCase:
    """Labelled synthetic case: nameplate = peak month of the central-value potential.

    ``x_ch4`` does not change any screened output; the default is the skeleton's config value.
    """
    p = params if params is not None else load_parameters()
    probe = run_chain(
        p,
        cane_t=cane_t,
        crop_year=crop_year,
        ad_shares=SYNTHETIC_AD_SHARES,
        x_ch4=x_ch4,
        nameplate_biomethane_nm3_d=1.0,  # any value: the potential does not depend on it
    )
    peak = float((probe.sim["biomethane_potential_nm3"] / probe.sim["days"]).max())
    if not peak > 0:
        raise ValueError("synthetic case: the central-value potential is zero")
    return ReferenceCase(
        label="synthetic",
        basis=(
            f"SYNTHETIC, not a mill: {cane_t:g} t cane normalisation unit, crop year "
            f"{crop_year}, AD shares of the calibration mills, S0, nameplate = peak month of "
            "the central-value biomethane potential"
        ),
        cane_t=cane_t,
        crop_year=crop_year,
        ad_shares=dict(SYNTHETIC_AD_SHARES),
        x_ch4=x_ch4,
        nameplate_biomethane_nm3_d=peak,
    )


def mill_case(
    mill_id: str,
    crop_year: int,
    *,
    config_path: Path | str = SKELETON_MILLS_YAML,
    anp_path: Path | str = ANP_MONTHLY_CSV,
    strategy: str | None = None,
    x_ch4: float | None = None,
) -> ReferenceCase:
    """Case of a calibration mill, with the same inputs as :func:`engine.skeleton.run_skeleton`.

    Raises:
        MissingInputError: the crop year has no cane value (or S1 has no storage block).
    """
    mills, x_default = load_mill_configs(config_path)
    if mill_id not in mills:
        raise KeyError(f"unknown mill {mill_id!r}; known: {', '.join(sorted(mills))}")
    mill = mills[mill_id]
    strategy = strategy or mill.strategy
    missing = missing_inputs(mill, crop_year, strategy)
    if missing:
        raise MissingInputError(
            f"{mill_id} {crop_year}: missing {'; '.join(missing)} in {config_path}"
        )
    cane = mill.cane_t[crop_year]
    assert cane is not None
    ethanol = mill.ethanol_l.get(crop_year)
    storage = None
    if strategy == "S1":
        assert mill.storage is not None
        storage = storage_from_config(mill.storage)
    cap_biomethane, _ = nameplate_from_anp(load_anp_monthly(mill.anp_plant_id, anp_path), crop_year)
    return ReferenceCase(
        label=f"{mill_id}-{crop_year}",
        basis=(
            f"{mill.name}, crop year {crop_year}, strategy {strategy}; cane "
            f"[{cane.confidence}] {cane.source}; nameplate from ANP ({mill.anp_plant_id})"
        ),
        cane_t=cane.value,
        crop_year=crop_year,
        ad_shares=dict(mill.ad_shares),
        x_ch4=x_default if x_ch4 is None else float(x_ch4),
        nameplate_biomethane_nm3_d=cap_biomethane,
        storage=storage,
        ethanol_l=ethanol.value if ethanol is not None else None,
    )


def evaluate(case: ReferenceCase, params: Mapping[str, Param]) -> dict[str, float]:
    """The four :data:`OUTPUTS` for one parameter set (LCOB is NaN when nothing is delivered)."""
    r = run_chain(
        params,
        cane_t=case.cane_t,
        crop_year=case.crop_year,
        ad_shares=case.ad_shares,
        x_ch4=case.x_ch4,
        nameplate_biomethane_nm3_d=case.nameplate_biomethane_nm3_d,
        storage=case.storage,
        ethanol_l=case.ethanol_l,
    )
    return {
        "annual_biomethane_nm3": r.annual_biomethane_nm3,
        "capacity_factor_annual": r.capacity_factor_annual,
        "lcob_brl_per_nm3": r.lcob.lcob_brl_per_nm3 if r.lcob is not None else math.nan,
        "months_infeasible": float((~r.sim["feasible"].astype(bool)).sum()),
    }


def chain_param_ids(case: ReferenceCase, params: Mapping[str, Param]) -> tuple[str, ...]:
    """Registry ids the chain reads for ``case``."""
    return run_chain(
        params,
        cane_t=case.cane_t,
        crop_year=case.crop_year,
        ad_shares=case.ad_shares,
        x_ch4=case.x_ch4,
        nameplate_biomethane_nm3_d=case.nameplate_biomethane_nm3_d,
        storage=case.storage,
        ethanol_l=case.ethanol_l,
    ).param_ids


def local_elasticities(
    case: ReferenceCase,
    params: Mapping[str, Param],
    param_ids: Sequence[str],
    *,
    rel_step: float = 0.1,
) -> pd.DataFrame:
    """One-sided elasticities of each output to each row with a numeric central value.

    ``elasticity_down = (y(x) − y(x(1−δ))) / (δ · y(x))`` and
    ``elasticity_up = (y(x(1+δ)) − y(x)) / (δ · y(x))``. Both are kept because the chain has
    kinks: with the nameplate at the central-case peak, a higher value is curtailed (``up`` near
    0) while a lower one costs output in full (``down``). A pair row scales both components
    together. A step that leaves the valid domain of the row (a recovery above 100 %, say) gives
    NaN for that side, as does a zero or non-numeric central value.
    Columns: ``param_id``, ``confidence``, ``output``, ``elasticity_down``, ``elasticity_up``.
    """
    if not 0 < rel_step < 1:
        raise ValueError("rel_step must be in (0, 1)")
    rows = []
    for pid in param_ids:
        p = params[pid]
        m = _CENTRAL_PAIR_RE.match(p.raw_central)
        if m:
            centrals: tuple[float, ...] = (float(m.group(1)), float(m.group(2)))
        elif p.central is not None:
            centrals = (p.central,)
        else:
            centrals = ()
        if not centrals or any(c == 0 for c in centrals):
            rows.extend((pid, p.confidence, out, math.nan, math.nan) for out in OUTPUTS)
            continue
        y0 = evaluate(case, set_row(params, pid, centrals))
        up = _try_evaluate(case, set_row(params, pid, [c * (1 + rel_step) for c in centrals]))
        dn = _try_evaluate(case, set_row(params, pid, [c * (1 - rel_step) for c in centrals]))
        for out in OUTPUTS:
            base = y0[out]
            usable = bool(base) and math.isfinite(base)
            e_dn = (base - dn[out]) / (rel_step * base) if usable and dn is not None else math.nan
            e_up = (up[out] - base) / (rel_step * base) if usable and up is not None else math.nan
            rows.append((pid, p.confidence, out, e_dn, e_up))
    return pd.DataFrame(
        rows, columns=["param_id", "confidence", "output", "elasticity_down", "elasticity_up"]
    )


def _try_evaluate(case: ReferenceCase, params: Mapping[str, Param]) -> dict[str, float] | None:
    """:func:`evaluate`, or ``None`` when the values are outside a model's valid domain."""
    try:
        return evaluate(case, params)
    except ValueError:
        return None


@dataclass
class MorrisResult:
    """Outputs of :func:`morris_screen`.

    Attributes:
        run_id: ``morris-<case label>-<hash>`` over registry, case and settings.
        case: the reference case.
        settings: trajectories, levels, seed, rel_step.
        central: the four outputs at the registry central values.
        morris: one row per (output, factor): μ, μ*, σ, μ* confidence, ``mu_star_rel``, rank.
        priority: one row per screened factor: largest ``mu_star_rel`` over
            :data:`PRIORITY_OUTPUTS`, the output where it occurs, flag, source, rank.
        excluded: rows not screened, with reasons.
        elasticities: local elasticities of every chain row.
        summary: JSON-safe dict with all of the above plus the Gate 0 share.
    """

    run_id: str
    case: ReferenceCase
    settings: dict
    central: dict[str, float]
    morris: pd.DataFrame
    priority: pd.DataFrame
    excluded: list[Excluded]
    elasticities: pd.DataFrame
    summary: dict = field(default_factory=dict)
    out_path: Path | None = None


def morris_screen(
    case: ReferenceCase,
    params: Mapping[str, Param] | None = None,
    *,
    trajectories: int = 20,
    levels: int = 4,
    seed: int = 20261006,
    rel_step: float = 0.1,
) -> MorrisResult:
    """Run the Morris screen and the local elasticities for one reference case.

    Args:
        case: fixed inputs (:func:`synthetic_case` or :func:`mill_case`).
        params: registry parameters (default: ``registry/parameters.csv``).
        trajectories: Morris trajectories *r*; the chain runs ``r · (k + 1)`` times.
        levels: grid levels *p* (even; SALib default 4).
        seed: sampling and bootstrap seed, so the run is reproducible.
        rel_step: relative step of the local elasticities.
    """
    from SALib.analyze import morris as morris_analyze
    from SALib.sample import morris as morris_sample

    if trajectories < 2:
        raise ValueError("trajectories must be >= 2")
    p = dict(params if params is not None else load_parameters())
    ids = chain_param_ids(case, p)
    factors, excluded = factor_space(p, ids)
    if not factors:
        raise ValueError("no registry row with a numeric range: nothing to screen")
    central = evaluate(case, p)

    problem = {
        "num_vars": len(factors),
        "names": [f.pid for f in factors],
        "bounds": [[0.0, 1.0]] * len(factors),
    }
    x = morris_sample.sample(problem, trajectories, num_levels=levels, seed=seed)
    ys = {out: np.empty(len(x)) for out in OUTPUTS}
    for i, qs in enumerate(x):
        pi = p
        for f, q in zip(factors, qs, strict=True):
            pi = set_row(pi, f.pid, f.value_at(float(q)))
        y = evaluate(case, pi)
        for out in OUTPUTS:
            ys[out][i] = y[out]

    rows = []
    for out in OUTPUTS:
        if not np.all(np.isfinite(ys[out])):
            raise ValueError(f"{out}: non-finite values in the Morris sample")
        si = morris_analyze.analyze(problem, x, ys[out], num_levels=levels, seed=seed)
        base = central[out]
        for j, f in enumerate(factors):
            mu_star = float(si["mu_star"][j])
            rows.append(
                {
                    "output": out,
                    "param_id": f.pid,
                    "confidence": f.confidence,
                    "mu": float(si["mu"][j]),
                    "mu_star": mu_star,
                    "sigma": float(si["sigma"][j]),
                    "mu_star_conf": float(si["mu_star_conf"][j]),
                    "mu_star_rel": mu_star / abs(base) if base else math.nan,
                }
            )
    morris = pd.DataFrame(rows)
    morris["rank"] = (
        morris.groupby("output")["mu_star"].rank(ascending=False, method="min").astype(int)
    )
    morris = morris.sort_values(["output", "rank", "param_id"], ignore_index=True)

    pri = morris[morris["output"].isin(PRIORITY_OUTPUTS)]
    best = pri.loc[pri.groupby("param_id")["mu_star_rel"].idxmax()]
    by_id = {f.pid: f for f in factors}
    priority = pd.DataFrame(
        {
            "param_id": best["param_id"],
            "confidence": best["confidence"],
            "max_mu_star_rel": best["mu_star_rel"],
            "output": best["output"],
            "unit": [by_id[i].unit for i in best["param_id"]],
            "source": [by_id[i].source for i in best["param_id"]],
        }
    ).sort_values(["max_mu_star_rel", "param_id"], ascending=[False, True], ignore_index=True)
    priority.insert(0, "rank", range(1, len(priority) + 1))

    elasticities = local_elasticities(case, p, ids, rel_step=rel_step)
    settings = {
        "trajectories": trajectories,
        "levels": levels,
        "seed": seed,
        "rel_step": rel_step,
        "n_evaluations": int(len(x)),
    }
    registry_hash = param_hash(p)
    run_hash = param_hash(
        {"registry": registry_hash, "case": case.to_dict(), "settings": settings}, length=10
    )
    run_id = f"morris-{case.label}-{run_hash}"
    result = MorrisResult(
        run_id=run_id,
        case=case,
        settings=settings,
        central=central,
        morris=morris,
        priority=priority,
        excluded=excluded,
        elasticities=elasticities,
    )
    result.summary = _summary(result, registry_hash)
    return result


def gate0_share(priority: pd.DataFrame, top_n: int = GATE0_TOP_N) -> dict:
    """Share of ``V`` rows among the top ``top_n`` screened rows with a non-zero effect."""
    moving = priority[priority["max_mu_star_rel"] > 0].head(top_n)
    n_v = int((moving["confidence"] == "V").sum())
    return {
        "top_n": top_n,
        "n_ranked": int(len(moving)),
        "n_v": n_v,
        "share_v": n_v / len(moving) if len(moving) else math.nan,
        "target": 0.6,
    }


def _jsonable(obj: object) -> object:
    if isinstance(obj, dict):
        return {str(k): _jsonable(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_jsonable(v) for v in obj]
    if isinstance(obj, float) and not math.isfinite(obj):
        return None
    if isinstance(obj, np.generic):
        return _jsonable(obj.item())
    return obj


def _max_abs(values: np.ndarray) -> float | None:
    finite = np.abs(values[np.isfinite(values)])
    return float(finite.max()) if finite.size else None


def _summary(r: MorrisResult, registry_hash: str) -> dict:
    zero = sorted(r.priority.loc[r.priority["max_mu_star_rel"] == 0, "param_id"])
    no_range = r.elasticities[
        r.elasticities["param_id"].isin([e.pid for e in r.excluded])
        & r.elasticities["output"].isin(PRIORITY_OUTPUTS)
    ]
    return _jsonable(
        {
            "run_id": r.run_id,
            "engine_version": __version__,
            "git_commit": _git_commit(),
            "param_hash": registry_hash,
            "case": r.case.to_dict(),
            "settings": r.settings,
            "central": r.central,
            "priority": r.priority.to_dict(orient="records"),
            "no_effect_in_this_case": zero,
            "gate0": gate0_share(r.priority),
            "excluded": [asdict(e) for e in r.excluded],
            "excluded_max_abs_elasticity": {
                pid: _max_abs(g[["elasticity_down", "elasticity_up"]].to_numpy())
                for pid, g in no_range.groupby("param_id")
            },
            "not_screened_inputs": NOT_SCREENED,
            "caveats": [
                "Screen over registry ranges (mostly S/K flags): it ranks what to verify, it is "
                "not an uncertainty estimate.",
                "Uniform sampling over [low, high] is a screening choice, not a distribution.",
                "The synthetic case is not a mill; its numbers are not results (ADR-0010).",
            ],
        }
    )


def write_outputs(result: MorrisResult, out_dir: Path | str = DEFAULT_OUT_DIR) -> Path:
    """Write ``morris.csv``, ``priority.csv``, ``elasticities.csv`` and ``summary.json``."""
    path = Path(out_dir) / result.run_id
    path.mkdir(parents=True, exist_ok=True)
    result.morris.to_csv(path / "morris.csv", index=False)
    result.priority.to_csv(path / "priority.csv", index=False)
    result.elasticities.to_csv(path / "elasticities.csv", index=False)
    (path / "summary.json").write_text(
        json.dumps(result.summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    result.out_path = path
    return path


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m engine.sensitivity", description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    m = sub.add_parser("morris", help="Morris screen + local elasticities of the skeleton")
    case = m.add_mutually_exclusive_group(required=True)
    case.add_argument("--synthetic", action="store_true", help="labelled synthetic case")
    case.add_argument("--mill", help="calibration mill id in skeleton_mills.yaml")
    m.add_argument("--crop-year", type=int, help="crop year (mill case; synthetic default 2025)")
    m.add_argument("--strategy", choices=("S0", "S1"), help="mill case only")
    m.add_argument("--trajectories", type=int, default=20)
    m.add_argument("--levels", type=int, default=4)
    m.add_argument("--seed", type=int, default=20261006)
    m.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR)
    m.add_argument("--no-write", action="store_true", help="print only")
    a = ap.parse_args(argv)

    if a.synthetic:
        ref = synthetic_case(crop_year=a.crop_year or 2025)
    else:
        if a.crop_year is None:
            ap.error("--mill needs --crop-year")
        try:
            ref = mill_case(a.mill, a.crop_year, strategy=a.strategy)
        except MissingInputError as exc:
            print(f"cannot run: {exc}")
            return 2
    res = morris_screen(ref, trajectories=a.trajectories, levels=a.levels, seed=a.seed)
    print(f"run_id {res.run_id}")
    print(f"case   {ref.basis}")
    print("central: " + ", ".join(f"{k}={v:.4g}" for k, v in res.central.items()))
    print(f"\npriority (max mu*/|y| over {', '.join(PRIORITY_OUTPUTS)}):")
    for row in res.priority.itertuples():
        print(
            f"  {row.rank:>2}  {row.param_id:<20} [{row.confidence}]  "
            f"{row.max_mu_star_rel:7.3f}  ({row.output})"
        )
    print("\nexcluded from the screen:")
    for e in res.excluded:
        print(f"  {e.pid:<20} [{e.confidence}]  {e.reason}")
    g = res.summary["gate0"]
    print(f"\nGate 0: {g['n_v']}/{g['n_ranked']} of the top {g['top_n']} moving rows are V")
    if not a.no_write:
        print(f"written to {write_outputs(res, a.out)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
