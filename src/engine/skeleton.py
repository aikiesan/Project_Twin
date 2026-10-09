"""Walking-skeleton runner (ADR-0010): cane → residues → CSTR → LCOB, compared with ANP monthly.

One run is one calibration mill and one crop year (April to March):

1. cane crushed (and optionally ethanol) from ``registry/skeleton_mills.yaml``, each value with
   its source and flag; the run stops if the crop year has no cane value;
2. monthly residues and the digester feed (:mod:`engine.supply.residues`);
3. digester sized for the worst month and the monthly mass balance
   (:mod:`engine.process.mass_balance`), with the ANP biomethane capacity as nameplate;
4. annuity LCOB on the delivered biomethane (:mod:`engine.economics.lcob`);
5. monthly comparison with the ANP plant series in ``evidence/`` (docs/13 §3.2), on the basis set
   per mill (``anp_volume_basis``: simulated biogas or biomethane, docs/13 §6).

Every run gets a deterministic ``run_id`` built from the registry hash, the mill inputs and the
ANP file, and writes ``monthly.csv``, ``comparison.csv`` and ``summary.json`` to
``data/processed/skeleton/<run_id>/``. Strategies S0 (no storage) and S1 (stored filter
cake, :mod:`engine.process.strategies`) are implemented.

The numbers rest on ``S``/``K`` parameters: they are v0 diagnostics, never results to publish
or export to PILAR-2b (ADR-0010).

Usage::

    python -m engine.skeleton list
    python -m engine.skeleton run --mill costa_pinto --crop-year 2025 [--x-ch4 0.65]
    python -m engine.skeleton run --mill narandiba --crop-year 2025 --strategy S1
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import subprocess
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import yaml

from engine import DATA_DIR, EVIDENCE_DIR, REGISTRY_DIR, ROOT, __version__
from engine.economics.lcob import (
    LcobResult,
    compare_with_anchors,
    economics_from_registry,
    lcob_from_registry,
)
from engine.process.mass_balance import (
    PlantDesign,
    limits_from_registry,
    simulate,
    size_digester,
    substrates_from_registry,
)
from engine.process.strategies import StorageS1, apply_s1_storage, storage_balance
from engine.registry import CONFIDENCE_FLAGS, Param, load_parameters, param_hash
from engine.supply.residues import (
    FEED_SUBSTRATES,
    coefficients_from_registry,
    monthly_residues,
    to_feed,
)

SKELETON_MILLS_YAML = REGISTRY_DIR / "skeleton_mills.yaml"
ANP_MONTHLY_CSV = EVIDENCE_DIR / "anp_monthly_sp_plants_from_pilar2b.csv"
DEFAULT_OUT_DIR = DATA_DIR / "processed" / "skeleton"

#: Strategies the runner can simulate (docs/10 §3).
IMPLEMENTED_STRATEGIES = ("S0", "S1")

#: Keys of the ``storage`` block (strategy S1); ``release_shares`` is optional.
STORAGE_KEYS = ("store_frac", "store_months", "release_months", "loss_frac_per_month")

#: Off-season calendar months used for the off-season share (docs/09 Step 5).
OFF_SEASON_MONTHS = (12, 1, 2, 3)

#: ANP months below this utilization (% of the capacity on the comparison basis) are flagged as
#: possible reporting gaps or stops and left out of the metrics (docs/13 §3.2: zeros are missing
#: unless confirmed). A v0 rule, stated here so it shows in every summary.
ANP_NEAR_ZERO_UTIL_PCT = 1.0

#: What the ANP plant field "Volume Processado de Biogás" is compared with (docs/13 §6): its
#: name says biogas, but at Narandiba it tracks biomethane (docs/21 C40, not confirmed by ANP, Q9).
ANP_VOLUME_BASES = ("biogas", "biomethane")

#: Caveats written into every summary.
CAVEATS = (
    "v0 walking skeleton (ADR-0010): most parameters are S or K; diagnostics, not results",
    "ANP volumes and capacities are m3 with no stated reference conditions (docs/21 C11); "
    "compared as Nm3",
    "the ANP field 'Volume Processado de Biogás' is compared with simulated biogas or "
    "biomethane as set per mill (anp_volume_basis); what it holds is unconfirmed (docs/21 Q9, C40)",
    "S0: no storage, so off-season output is zero by construction. S1: one silo pool with a "
    "constant fresh-mass loss per month (v0); its cake-only off-season feed fails the TS check, "
    "because digestate recirculation is not modelled (engine.process.strategies)",
    "harvest profile: uniform April-November until the UNICA series is in (docs/09 §5)",
    "LCOB: no price-year escalation, taxes or revenues (docs/11 §9)",
)


class MissingInputError(ValueError):
    """A mill input the run needs is empty in ``skeleton_mills.yaml``."""


@dataclass(frozen=True)
class Observation:
    """One observed value with its provenance (docs/08 flags)."""

    value: float
    source: str
    confidence: str


@dataclass(frozen=True)
class MillConfig:
    """Inputs for one calibration mill, as read from ``skeleton_mills.yaml``."""

    id: str
    name: str
    anp_plant_id: str
    strategy: str
    cane_t: Mapping[int, Observation | None]
    ethanol_l: Mapping[int, Observation | None]
    ad_shares: Mapping[str, float]
    storage: Mapping[str, object] | None = None
    anp_volume_basis: str = "biogas"
    notes: str = ""


def _observation(raw: object, where: str) -> Observation | None:
    if not isinstance(raw, Mapping):
        raise ValueError(f"{where}: expected a mapping with value, source, confidence")
    value = raw.get("value")
    if value is None:
        return None
    source = str(raw.get("source") or "").strip()
    confidence = str(raw.get("confidence") or "").strip()
    if not source or source.upper() == "TODO":
        raise ValueError(f"{where}: a value needs its source")
    if confidence not in CONFIDENCE_FLAGS:
        raise ValueError(f"{where}: confidence must be one of {CONFIDENCE_FLAGS}")
    value = float(value)
    if value < 0:
        raise ValueError(f"{where}: value must be >= 0")
    return Observation(value=value, source=source, confidence=confidence)


def _by_year(raw: object, where: str) -> dict[int, Observation | None]:
    raw = raw or {}
    if not isinstance(raw, Mapping):
        raise ValueError(f"{where}: expected a mapping of crop year -> entry")
    return {int(y): _observation(v, f"{where}[{y}]") for y, v in raw.items()}


def _storage_block(raw: object, where: str) -> dict | None:
    """Raw S1 settings, or ``None``. Values may be null until filled; checked when S1 runs."""
    if raw is None:
        return None
    if not isinstance(raw, Mapping):
        raise ValueError(f"{where}: expected a mapping")
    unknown = set(raw) - {*STORAGE_KEYS, "release_shares", "loss_source", "notes"}
    if unknown:
        raise ValueError(f"{where}: unknown key(s) {', '.join(sorted(unknown))}")
    return dict(raw)


def storage_from_config(block: Mapping[str, object]) -> StorageS1:
    """Build :class:`StorageS1` from a filled ``storage`` block (raises if a value is empty)."""
    empty = [k for k in STORAGE_KEYS if block.get(k) is None]
    source = str(block.get("loss_source") or "").strip()
    if not source or source.upper() == "TODO":
        empty.append("loss_source")
    if empty:
        raise MissingInputError("storage needs " + ", ".join(empty))
    shares = block.get("release_shares")
    return StorageS1(
        store_frac=float(block["store_frac"]),  # type: ignore[arg-type]
        store_months=tuple(int(m) for m in block["store_months"]),  # type: ignore[union-attr]
        release_months=tuple(int(m) for m in block["release_months"]),  # type: ignore[union-attr]
        loss_frac_per_month=float(block["loss_frac_per_month"]),  # type: ignore[arg-type]
        release_shares=tuple(float(x) for x in shares) if shares else None,  # type: ignore[union-attr]
    )


def load_mill_configs(
    path: Path | str = SKELETON_MILLS_YAML,
) -> tuple[dict[str, MillConfig], float]:
    """Read and check ``skeleton_mills.yaml``. Returns ``(mills, x_ch4)``."""
    doc = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    x_ch4 = doc.get("x_ch4")
    if x_ch4 is None or not 0 < float(x_ch4) <= 1:
        raise ValueError(f"{path}: x_ch4 must be a fraction in (0, 1]")
    mills: dict[str, MillConfig] = {}
    for mill_id, m in (doc.get("mills") or {}).items():
        where = f"{path}:{mill_id}"
        shares = {k: float(v) for k, v in (m.get("ad_shares") or {}).items()}
        if set(shares) != set(FEED_SUBSTRATES):
            raise ValueError(f"{where}: ad_shares needs exactly {', '.join(FEED_SUBSTRATES)}")
        if any(not 0 <= v <= 1 for v in shares.values()):
            raise ValueError(f"{where}: ad_shares must be fractions in [0, 1]")
        for key in ("name", "anp_plant_id", "strategy"):
            if not m.get(key):
                raise ValueError(f"{where}: missing {key}")
        basis = str(m.get("anp_volume_basis") or "biogas")
        if basis not in ANP_VOLUME_BASES:
            raise ValueError(f"{where}: anp_volume_basis must be one of {ANP_VOLUME_BASES}")
        mills[mill_id] = MillConfig(
            id=mill_id,
            name=str(m["name"]),
            anp_plant_id=str(m["anp_plant_id"]),
            strategy=str(m["strategy"]),
            cane_t=_by_year(m.get("cane_t"), f"{where}.cane_t"),
            ethanol_l=_by_year(m.get("ethanol_l"), f"{where}.ethanol_l"),
            ad_shares=shares,
            storage=_storage_block(m.get("storage"), f"{where}.storage"),
            anp_volume_basis=basis,
            notes=str(m.get("notes") or ""),
        )
    return mills, float(x_ch4)


def missing_inputs(mill: MillConfig, crop_year: int, strategy: str | None = None) -> list[str]:
    """What the run of ``crop_year`` still needs (empty list = ready).

    ``strategy`` overrides the mill's configured strategy (as ``--strategy`` does).
    """
    strategy = strategy or mill.strategy
    missing = []
    if mill.cane_t.get(crop_year) is None:
        missing.append(f"cane_t[{crop_year}]")
    if strategy not in IMPLEMENTED_STRATEGIES:
        missing.append(f"strategy {strategy} (implemented: {', '.join(IMPLEMENTED_STRATEGIES)})")
    elif strategy == "S1":
        if mill.storage is None:
            missing.append("storage block (strategy S1)")
        else:
            try:
                storage_from_config(mill.storage)
            except MissingInputError as exc:
                missing.append(str(exc))
    return missing


def load_anp_monthly(plant_id: str, path: Path | str = ANP_MONTHLY_CSV) -> pd.DataFrame:
    """ANP monthly rows of one plant, with ``month`` as ``"YYYY-MM"``."""
    df = pd.read_csv(path)
    df = df[df["plant_id"] == plant_id].copy()
    if df.empty:
        raise KeyError(f"no ANP rows for plant_id {plant_id!r} in {path}")
    df["month"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m")
    cols = ["month", "cap_biometano_m3d", "cap_biogas_m3d", "vol_biogas_m3d", "util_pct"]
    return df[cols].sort_values("month").reset_index(drop=True)


def _crop_year_months(crop_year: int) -> list[str]:
    return [f"{crop_year}-{m:02d}" for m in range(4, 13)] + [
        f"{crop_year + 1}-{m:02d}" for m in range(1, 4)
    ]


def nameplate_from_anp(anp: pd.DataFrame, crop_year: int) -> tuple[float, float]:
    """``(biomethane, biogas)`` capacity in m³/d: latest month of the crop year, else latest."""
    in_year = anp[anp["month"].isin(_crop_year_months(crop_year))]
    row = (in_year if not in_year.empty else anp).iloc[-1]
    return float(row["cap_biometano_m3d"]), float(row["cap_biogas_m3d"])


def compare_with_anp(
    sim: pd.DataFrame,
    anp: pd.DataFrame,
    cap_m3_d: float,
    *,
    basis: str = "biogas",
    near_zero_util_pct: float = ANP_NEAR_ZERO_UTIL_PCT,
) -> tuple[pd.DataFrame, dict]:
    """Monthly simulated vs observed output, on the basis of the ANP plant field.

    The ANP plant series is "Volume Processado de Biogás" (m³/d, ``vol_biogas_m3d``). ``basis``
    says what it is compared with: simulated ``"biogas"`` (the field's name) or ``"biomethane"``
    (where company reports show the field tracks biomethane, Narandiba, docs/21 C40).
    ``cap_m3_d`` is the ANP capacity on the same basis. Simulated output is capped at it (a plant
    cannot report more), and utilization is output / capacity for both series. ANP months below
    ``near_zero_util_pct`` are flagged ``obs_near_zero`` and left out of the metrics.

    Returns:
        The monthly table (``sim_nm3_d``, ``sim_capped_nm3_d``, ``sim_util_pct``,
        ``obs_anp_m3_d``, ``obs_util_pct``, ``obs_near_zero``, ``basis``) and a metrics dict:
        ``basis``, ``n_months_observed``, ``n_months_compared``, ``n_obs_near_zero``,
        ``mae_util_pp``, ``bias_util_pp`` (simulated − observed), ``volume_ratio_sim_obs``,
        ``offseason_share_sim``, ``offseason_share_obs``.
    """
    if basis not in ANP_VOLUME_BASES:
        raise ValueError(f"basis must be one of {ANP_VOLUME_BASES}")
    if cap_m3_d <= 0:
        raise ValueError("cap_m3_d must be > 0")
    col = f"{basis}_nm3"
    t = sim[["month", "days", col]].copy()
    t["sim_nm3_d"] = t[col] / t["days"]
    t["sim_capped_nm3_d"] = t["sim_nm3_d"].clip(upper=cap_m3_d)
    t["sim_util_pct"] = 100 * t["sim_capped_nm3_d"] / cap_m3_d
    obs = anp[["month", "vol_biogas_m3d"]].rename(columns={"vol_biogas_m3d": "obs_anp_m3_d"})
    t = t.drop(columns=col).merge(obs, on="month", how="left")
    t["obs_util_pct"] = 100 * t["obs_anp_m3_d"] / cap_m3_d
    # object dtype keeps three states: True / False / None (month not in the ANP series)
    t["obs_near_zero"] = pd.Series(
        [None if math.isnan(u) else bool(u < near_zero_util_pct) for u in t["obs_util_pct"]],
        dtype=object,
    )
    t["basis"] = basis
    observed = t[t["obs_anp_m3_d"].notna()]
    used = observed[~observed["obs_near_zero"].astype(bool)]

    def share_off(vol_d: pd.Series, frame: pd.DataFrame) -> float | None:
        vol = vol_d * frame["days"]
        total = vol.sum()
        if total <= 0:
            return None
        off = frame["month"].str[5:7].astype(int).isin(OFF_SEASON_MONTHS)
        return float(vol[off].sum() / total)

    metrics: dict = {
        "basis": basis,
        "n_months_observed": int(len(observed)),
        "n_months_compared": int(len(used)),
        "n_obs_near_zero": int(observed["obs_near_zero"].astype(bool).sum()),
        "near_zero_util_pct": near_zero_util_pct,
        "mae_util_pp": None,
        "bias_util_pp": None,
        "volume_ratio_sim_obs": None,
        "offseason_share_sim": None,
        "offseason_share_obs": None,
    }
    if not used.empty:
        diff = used["sim_util_pct"] - used["obs_util_pct"]
        obs_vol = (used["obs_anp_m3_d"] * used["days"]).sum()
        sim_vol = (used["sim_capped_nm3_d"] * used["days"]).sum()
        metrics.update(
            mae_util_pp=float(diff.abs().mean()),
            bias_util_pp=float(diff.mean()),
            volume_ratio_sim_obs=float(sim_vol / obs_vol) if obs_vol > 0 else None,
            offseason_share_sim=share_off(used["sim_capped_nm3_d"], used),
            offseason_share_obs=share_off(used["obs_anp_m3_d"], used),
        )
    return t, metrics


def _git_commit() -> str | None:
    def git(*args: str) -> str:
        try:
            return subprocess.run(
                ["git", *args], cwd=ROOT, capture_output=True, text=True, check=True
            ).stdout.strip()
        except (OSError, subprocess.CalledProcessError):
            return ""

    commit = git("rev-parse", "--short", "HEAD")
    if not commit:
        return None
    return f"{commit}+dirty" if git("status", "--porcelain", "--", "src", "registry") else commit


def _file_sha256(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


@dataclass
class ChainResult:
    """Steps 1-4 of one skeleton run, before the ANP comparison and any file output.

    Attributes:
        residues: monthly residue table (after S1 storage when ``storage`` is given).
        sim: monthly mass balance (:func:`engine.process.mass_balance.simulate`).
        digester_volume_m3: digester sized for the worst month.
        annual_biomethane_nm3: delivered biomethane over the crop year, Nm³.
        capacity_factor_annual: delivered / (nameplate × days in the crop year).
        lcob: annuity LCOB, ``None`` when nothing is delivered.
        param_ids: every registry id the chain read, sorted.
    """

    residues: pd.DataFrame
    sim: pd.DataFrame
    digester_volume_m3: float
    annual_biomethane_nm3: float
    capacity_factor_annual: float
    lcob: LcobResult | None
    param_ids: tuple[str, ...]


def run_chain(
    params: Mapping[str, Param],
    *,
    cane_t: float,
    crop_year: int,
    ad_shares: Mapping[str, float],
    x_ch4: float,
    nameplate_biomethane_nm3_d: float,
    storage: StorageS1 | None = None,
    ethanol_l: float | None = None,
) -> ChainResult:
    """Cane → residues → feed → CSTR → LCOB for one crop year (no I/O).

    This is the part of :func:`run_skeleton` that the sensitivity screen
    (:mod:`engine.sensitivity`) re-runs with perturbed registry rows.

    Args:
        params: registry parameters (central values are used).
        cane_t: cane crushed in the crop year, t.
        crop_year: year in which the season starts (April).
        ad_shares: share of each generated stream sent to AD (``vinasse``, ``filter_cake``,
            ``straw``), fractions.
        x_ch4: biogas CH₄ fraction (affects biogas, not biomethane).
        nameplate_biomethane_nm3_d: upgrading nameplate, Nm³/d of biomethane.
        storage: S1 settings; ``None`` runs S0.
        ethanol_l: ethanol produced, L (default: cane × ``ethanol_yield``).
    """
    coeffs = coefficients_from_registry(params)
    residues = monthly_residues(
        cane_t,
        crop_year,
        coeffs,
        vinasse_to_ad_frac=ad_shares["vinasse"],
        filter_cake_to_ad_frac=ad_shares["filter_cake"],
        straw_to_ad_frac=ad_shares["straw"],
        ethanol_l=ethanol_l,
    )
    if storage is not None:
        residues = apply_s1_storage(residues, storage)
    subs = substrates_from_registry(params)
    feed = to_feed(residues, vinasse_density_t_per_m3=subs["vinasse"].density_t_per_m3)

    limits = limits_from_registry(params)
    volume = size_digester(feed, subs, limits)
    design = PlantDesign(
        digester_volume_m3=volume,
        upgrading_capacity_nm3_d=nameplate_biomethane_nm3_d,
        x_ch4=x_ch4,
        ch4_recovery_frac=params["upg_ch4_recovery"].require_central() / 100,
    )
    sim = simulate(feed, subs, design, limits)  # all 12 months, off-season feed is zero

    annual_bm = float(sim["biomethane_nm3"].sum())
    lcob = (
        lcob_from_registry(nameplate_biomethane_nm3_d, annual_bm, params) if annual_bm > 0 else None
    )
    param_ids = sorted(
        set(coeffs.param_ids)
        | {pid for f in FEED_SUBSTRATES for pid in subs[f].param_ids}
        | set(limits.param_ids)
        | set(economics_from_registry(params).param_ids)
        | {"upg_ch4_recovery"}
    )
    return ChainResult(
        residues=residues,
        sim=sim,
        digester_volume_m3=volume,
        annual_biomethane_nm3=annual_bm,
        capacity_factor_annual=annual_bm / (nameplate_biomethane_nm3_d * float(sim["days"].sum())),
        lcob=lcob,
        param_ids=tuple(param_ids),
    )


@dataclass
class SkeletonRun:
    """Outputs of one run (also written to disk when an output folder is given)."""

    run_id: str
    monthly: pd.DataFrame
    comparison: pd.DataFrame
    summary: dict
    out_path: Path | None = field(default=None)


def run_skeleton(
    mill_id: str,
    crop_year: int,
    *,
    config_path: Path | str = SKELETON_MILLS_YAML,
    anp_path: Path | str = ANP_MONTHLY_CSV,
    params: Mapping[str, Param] | None = None,
    x_ch4: float | None = None,
    strategy: str | None = None,
    brl_per_usd: float | None = None,
    out_dir: Path | str | None = DEFAULT_OUT_DIR,
) -> SkeletonRun:
    """Run the skeleton for one mill and crop year (see the module docstring).

    Args:
        mill_id: key in ``skeleton_mills.yaml``.
        crop_year: year in which the season starts (April).
        config_path, anp_path: inputs; defaults are the registry file and the ANP evidence CSV.
        params: registry parameters (default: ``registry/parameters.csv``).
        x_ch4: biogas CH₄ fraction; default is the config value (docs/21 C13).
        strategy: ``"S0"`` or ``"S1"``; default is the mill's configured strategy.
        brl_per_usd: exchange rate for the US$/MMBtu anchor; ``None`` leaves it unevaluated.
        out_dir: parent folder for ``<run_id>/``; ``None`` writes nothing.

    Raises:
        MissingInputError: the crop year has no cane value, the strategy is not implemented,
            or S1 runs without a filled ``storage`` block.
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
    x = x_default if x_ch4 is None else float(x_ch4)
    p = params if params is not None else load_parameters()
    registry_hash = param_hash() if params is None else param_hash(p)
    cane = mill.cane_t[crop_year]
    ethanol = mill.ethanol_l.get(crop_year)
    assert cane is not None  # checked by missing_inputs

    storage = None
    if strategy == "S1":
        assert mill.storage is not None  # checked by missing_inputs
        storage = storage_from_config(mill.storage)
    anp = load_anp_monthly(mill.anp_plant_id, anp_path)
    cap_biomethane, cap_biogas = nameplate_from_anp(anp, crop_year)

    # 1-4. residues, feed, digester and mass balance, LCOB
    chain = run_chain(
        p,
        cane_t=cane.value,
        crop_year=crop_year,
        ad_shares=mill.ad_shares,
        x_ch4=x,
        nameplate_biomethane_nm3_d=cap_biomethane,
        storage=storage,
        ethanol_l=ethanol.value if ethanol is not None else None,
    )
    residues, sim, lcob = chain.residues, chain.sim, chain.lcob
    monthly = residues.merge(sim, on="month", how="left")
    anchors = (
        compare_with_anchors(lcob.lcob_brl_per_nm3, brl_per_usd=brl_per_usd, params=p)
        if lcob is not None
        else None
    )

    # 5. comparison with ANP, on the mill's basis
    basis = mill.anp_volume_basis
    cap = cap_biogas if basis == "biogas" else cap_biomethane
    comparison, metrics = compare_with_anp(sim, anp, cap, basis=basis)

    used_ids = chain.param_ids
    flags = {pid: p[pid].confidence for pid in used_ids}
    inputs = {
        "cane_t": asdict(cane),
        "ethanol_l": asdict(ethanol) if ethanol is not None else None,
        "ad_shares": dict(mill.ad_shares),
        "x_ch4": x,
        "strategy": strategy,
        "storage": (
            {**asdict(storage), "loss_source": str(mill.storage.get("loss_source"))}
            if storage is not None and mill.storage is not None
            else None
        ),
        "anp_plant_id": mill.anp_plant_id,
        "anp_volume_basis": basis,
        "anp_file_sha256": _file_sha256(anp_path),
    }
    run_id = (
        f"skel-{mill_id}-{crop_year}-"
        f"{param_hash({'registry': registry_hash, 'inputs': inputs}, length=10)}"
    )
    summary = {
        "run_id": run_id,
        "created_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "engine_version": __version__,
        "git_commit": _git_commit(),
        "param_hash": registry_hash,
        "mill": {"id": mill.id, "name": mill.name},
        "crop_year": crop_year,
        "inputs": inputs,
        "nameplate": {
            "cap_biometano_m3_d": cap_biomethane,
            "cap_biogas_m3_d": cap_biogas,
            "source": "ANP monthly via PILAR-2b (evidence/); m3 basis not stated (docs/21 C11)",
        },
        "digester_volume_m3": chain.digester_volume_m3,
        "registry_params": flags,
        "flag_counts": dict(Counter(flags.values())),
        "results": {
            "annual_biomethane_nm3": chain.annual_biomethane_nm3,
            "capacity_factor_annual": chain.capacity_factor_annual,
            "months_infeasible": [
                m for m, ok in zip(sim["month"], sim["feasible"], strict=True) if not ok
            ],
            "storage_balance": storage_balance(residues) if storage is not None else None,
            "lcob": asdict(lcob) if lcob is not None else None,
            "anchors": anchors.to_dict(orient="records") if anchors is not None else None,
        },
        "comparison_with_anp": metrics,
        "caveats": list(CAVEATS),
    }
    summary = _clean(summary)  # same JSON-safe values in memory as in summary.json
    run = SkeletonRun(run_id=run_id, monthly=monthly, comparison=comparison, summary=summary)
    if out_dir is not None:
        path = Path(out_dir) / run_id
        path.mkdir(parents=True, exist_ok=True)
        monthly.to_csv(path / "monthly.csv", index=False)
        comparison.to_csv(path / "comparison.csv", index=False)
        (path / "summary.json").write_text(
            json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
        run.out_path = path
    return run


def _clean(obj: object) -> object:
    """JSON-safe copy: NaN -> None, numpy scalars -> Python."""
    if isinstance(obj, Mapping):
        return {str(k): _clean(v) for k, v in obj.items()}
    if isinstance(obj, list | tuple):
        return [_clean(v) for v in obj]
    item = getattr(obj, "item", None)
    if callable(item) and getattr(obj, "shape", None) == ():
        obj = item()
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if obj is pd.NA:
        return None
    return obj


def _fmt(v: object, spec: str = ".3g") -> str:
    return "n/a" if v is None else format(v, spec)


def main(argv: Sequence[str] | None = None) -> int:
    """CLI: ``list`` the mills and what they miss; ``run`` one mill and crop year."""
    parser = argparse.ArgumentParser(
        prog="python -m engine.skeleton", description=__doc__.split("\n")[0]
    )
    parser.add_argument("--config", type=Path, default=SKELETON_MILLS_YAML)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="mills, crop years and missing inputs")
    p_run = sub.add_parser("run", help="run one mill and crop year")
    p_run.add_argument("--mill", required=True)
    p_run.add_argument("--crop-year", type=int, required=True)
    p_run.add_argument("--x-ch4", type=float, default=None, help="override the config x_ch4")
    p_run.add_argument("--strategy", choices=IMPLEMENTED_STRATEGIES, default=None)
    p_run.add_argument("--brl-per-usd", type=float, default=None, help="for the US$ anchor")
    p_run.add_argument("--anp", type=Path, default=ANP_MONTHLY_CSV)
    p_run.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR)
    args = parser.parse_args(argv)

    if args.command == "list":
        mills, x_ch4 = load_mill_configs(args.config)
        print(f"x_ch4 (config): {x_ch4}")
        for m in mills.values():
            for year in sorted(m.cane_t) or [None]:
                miss = missing_inputs(m, year) if year is not None else ["cane_t (no crop year)"]
                state = "ready" if not miss else "missing " + "; ".join(miss)
                print(f"{m.id:<14} {m.strategy:<3} {year}  {state}")
        return 0

    try:
        run = run_skeleton(
            args.mill,
            args.crop_year,
            config_path=args.config,
            anp_path=args.anp,
            x_ch4=args.x_ch4,
            strategy=args.strategy,
            brl_per_usd=args.brl_per_usd,
            out_dir=args.out,
        )
    except MissingInputError as exc:
        print(f"Cannot run: {exc}")
        return 2
    s = run.summary
    r, c = s["results"], s["comparison_with_anp"]
    lcob = r["lcob"]["lcob_brl_per_nm3"] if r["lcob"] else None
    print(f"run_id {run.run_id} -> {run.out_path}")
    print(
        f"  biomethane {r['annual_biomethane_nm3']:.4g} Nm3/yr, "
        f"CF {r['capacity_factor_annual']:.2f}"
    )
    print(f"  LCOB {_fmt(lcob)} R$/Nm3 (v0, S/K parameters; see caveats in summary.json)")
    print(
        f"  vs ANP ({c['basis']} basis): {c['n_months_compared']} months, "
        f"MAE {_fmt(c['mae_util_pp'])} pp, "
        f"bias {_fmt(c['bias_util_pp'])} pp, off-season share sim "
        f"{_fmt(c['offseason_share_sim'])} vs obs {_fmt(c['offseason_share_obs'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
