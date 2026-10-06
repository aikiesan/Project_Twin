"""Lab and pilot data → model parameters (experiments E1–E9, docs/17).

Reads the CSV templates in ``templates/lab/`` and turns them into quantities the engine uses:

- :func:`load_bmp` / :func:`net_specific_yield` — blank-corrected specific methane yield curves
  (NmL CH₄ per g VS added) per substrate and replicate.
- :func:`fit_first_order` — ``B(t) = B0·(1 − e^{−k t})`` (B0 → BMP, k → η_kin in
  ``engine.process``); :func:`fit_gompertz` — modified Gompertz (Bmax, Rmax, λ).
- :func:`bmp_validity` — validation checks with thresholds passed in (Holliger et al. 2016
  criteria — read the paper; nothing hard-coded).
- :func:`summarize_cstr` — daily reactor log → OLR, HRT, specific yield, stability indicators
  per period (feeds ``olr_max_cstr``, ``bmp_fullscale``, FOS/TAC).
- :func:`proposed_registry_rows` — draft ``parameters.csv`` lines with flag **V** and the
  experiment as source (a human reviews before committing).

Units: gas volumes are NmL (0 °C, 1 atm, dry); masses in g; volumes in L; time in days.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit

from engine.registry import PARAMETER_EVIDENCE_COLUMNS

BMP_REQUIRED = [
    "experiment_id",
    "substrate_id",
    "bottle_id",
    "role",
    "replicate",
    "inoculum_vs_g",
    "substrate_vs_g",
    "day",
    "cum_ch4_nml",
]
ROLES = {"sample", "blank", "positive_control"}


def load_bmp(path_or_df) -> pd.DataFrame:
    """Load and validate a BMP results table (``templates/lab/bmp_results_template.csv``).

    Raises ``ValueError`` listing every problem found (missing columns, bad roles, negative or
    decreasing cumulative volumes, blanks with substrate VS > 0, missing day-0 readings).
    """
    df = path_or_df.copy() if isinstance(path_or_df, pd.DataFrame) else pd.read_csv(path_or_df)
    problems: list[str] = []
    missing = [c for c in BMP_REQUIRED if c not in df.columns]
    if missing:
        raise ValueError(f"missing columns: {missing}")
    df = df[~df.get("notes", pd.Series("", index=df.index)).astype(str).str.contains("synthetic")]
    bad_roles = sorted(set(df["role"]) - ROLES)
    if bad_roles:
        problems.append(f"unknown role(s) {bad_roles}; allowed {sorted(ROLES)}")
    for col in ("inoculum_vs_g", "substrate_vs_g", "day", "cum_ch4_nml"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
        if df[col].isna().any():
            problems.append(f"non-numeric/blank values in {col}")
        if (df[col] < 0).any():
            problems.append(f"negative values in {col}")
    blanks = df[df["role"] == "blank"]
    if (blanks["substrate_vs_g"] > 0).any():
        problems.append("blank bottles must have substrate_vs_g = 0")
    for bottle, g in df.sort_values("day").groupby("bottle_id"):
        if (np.diff(g["cum_ch4_nml"].to_numpy()) < -1e-9).any():
            problems.append(f"bottle {bottle}: cumulative CH4 decreases")
        if g["day"].min() != 0:
            problems.append(f"bottle {bottle}: no day-0 reading")
    if problems:
        raise ValueError("; ".join(problems))
    return df.reset_index(drop=True)


def net_specific_yield(df: pd.DataFrame) -> pd.DataFrame:
    """Blank-corrected specific CH₄ yield per bottle and day (NmL CH₄ / g VS added).

    For each sample/positive-control bottle *i* at day *t*:

        Y_i(t) = [V_i(t) − V̄_blank(t) · (VS_inoc,i / VS̄_inoc,blank)] / VS_sub,i

    where V̄_blank(t) is the mean blank cumulative volume at the same day (blanks must share the
    reading days of the samples within an experiment) — the standard inoculum correction.
    """
    out = []
    for exp_id, e in df.groupby("experiment_id"):
        blanks = e[e["role"] == "blank"]
        if blanks.empty:
            raise ValueError(f"experiment {exp_id}: no blank bottles")
        blank_mean = blanks.groupby("day").agg(
            v_blank=("cum_ch4_nml", "mean"), vs_inoc_blank=("inoculum_vs_g", "mean")
        )
        s = e[e["role"] != "blank"].merge(blank_mean, left_on="day", right_index=True, how="left")
        if s["v_blank"].isna().any():
            days = sorted(s.loc[s["v_blank"].isna(), "day"].unique())
            raise ValueError(f"experiment {exp_id}: no blank reading on day(s) {days}")
        corr = s["v_blank"] * s["inoculum_vs_g"] / s["vs_inoc_blank"]
        s = s.assign(net_ch4_nml=s["cum_ch4_nml"] - corr)
        s = s.assign(yield_nml_per_gvs=s["net_ch4_nml"] / s["substrate_vs_g"])
        out.append(s)
    cols = ["experiment_id", "substrate_id", "bottle_id", "role", "replicate", "day"]
    return pd.concat(out)[cols + ["net_ch4_nml", "yield_nml_per_gvs"]].reset_index(drop=True)


@dataclass(frozen=True)
class KineticFit:
    """Result of a kinetic fit on one yield curve (units: NmL/g VS, days)."""

    model: str
    params: dict[str, float]
    stderr: dict[str, float]
    r2: float
    n: int


def _r2(y: np.ndarray, yhat: np.ndarray) -> float:
    ss_res = float(np.sum((y - yhat) ** 2))
    ss_tot = float(np.sum((y - y.mean()) ** 2))
    return 1.0 - ss_res / ss_tot if ss_tot > 0 else float("nan")


def first_order(t, b0, k):
    """``B0·(1 − exp(−k t))`` — B0 in NmL/g VS, k in 1/d."""
    return b0 * (1.0 - np.exp(-k * np.asarray(t, dtype=float)))


def gompertz(t, bmax, rmax, lag):
    """Modified Gompertz: ``Bmax·exp(−exp(Rmax·e/Bmax·(λ − t) + 1))``."""
    t = np.asarray(t, dtype=float)
    return bmax * np.exp(-np.exp(rmax * np.e / bmax * (lag - t) + 1.0))


def fit_first_order(days, yield_nml_gvs) -> KineticFit:
    """Least-squares fit of :func:`first_order`; initial guess from the data range."""
    t = np.asarray(days, dtype=float)
    y = np.asarray(yield_nml_gvs, dtype=float)
    b0_guess = float(np.nanmax(y)) or 1.0
    popt, pcov = curve_fit(first_order, t, y, p0=[b0_guess, 0.1], bounds=([0, 0], [np.inf, 10]))
    se = np.sqrt(np.diag(pcov))
    return KineticFit(
        "first_order",
        {"b0_nml_gvs": float(popt[0]), "k_per_d": float(popt[1])},
        {"b0_nml_gvs": float(se[0]), "k_per_d": float(se[1])},
        _r2(y, first_order(t, *popt)),
        len(t),
    )


def fit_gompertz(days, yield_nml_gvs) -> KineticFit:
    """Least-squares fit of :func:`gompertz` (Bmax NmL/g VS, Rmax NmL/g VS/d, λ d)."""
    t = np.asarray(days, dtype=float)
    y = np.asarray(yield_nml_gvs, dtype=float)
    bmax0 = float(np.nanmax(y)) or 1.0
    rmax0 = float(np.nanmax(np.diff(y) / np.maximum(np.diff(t), 1e-9))) if len(t) > 1 else 1.0
    popt, pcov = curve_fit(
        gompertz,
        t,
        y,
        p0=[bmax0, max(rmax0, 1e-3), 0.5],
        bounds=([0, 0, 0], [np.inf, np.inf, float(t.max())]),
        maxfev=20_000,
    )
    se = np.sqrt(np.diag(pcov))
    names = ["bmax_nml_gvs", "rmax_nml_gvs_d", "lag_d"]
    return KineticFit(
        "gompertz",
        dict(zip(names, map(float, popt), strict=True)),
        dict(zip(names, map(float, se), strict=True)),
        _r2(y, gompertz(t, *popt)),
        len(t),
    )


def bmp_validity(
    curves: pd.DataFrame,
    pc_theoretical_nml_gvs: float,
    pc_recovery_min: float,
    pc_recovery_max: float,
    rsd_max: float,
    end_daily_rate_max: float,
) -> pd.DataFrame:
    """Validation checks per experiment (thresholds REQUIRED — take them from Holliger 2016).

    Args:
        curves: output of :func:`net_specific_yield`.
        pc_theoretical_nml_gvs: theoretical yield of the positive control (e.g. cellulose).
        pc_recovery_min, pc_recovery_max: accepted positive-control recovery (fractions).
        rsd_max: maximum relative standard deviation among replicates at the final day (fraction).
        end_daily_rate_max: termination criterion — mean daily increment over the last
            reading interval as a fraction of the final cumulative yield.

    Returns one row per (experiment, substrate) with the computed statistics and pass flags.
    """
    rows = []
    for (exp_id, sub), g in curves.groupby(["experiment_id", "substrate_id"]):
        last_day = g["day"].max()
        final = g[g["day"] == last_day]["yield_nml_gvs"]
        mean = float(final.mean())
        rsd = float(final.std(ddof=1) / mean) if len(final) > 1 and mean else float("nan")
        mean_curve = g.groupby("day")["yield_nml_gvs"].mean().sort_index()
        if len(mean_curve) >= 2 and mean:
            # mean daily increment over the LAST reading interval (readings are often sparse,
            # e.g. weekly at the end), relative to the final cumulative yield
            dt = float(mean_curve.index[-1] - mean_curve.index[-2])
            daily = (mean_curve.iloc[-1] - mean_curve.iloc[-2]) / max(dt, 1e-9)
            end_rate = float(daily / mean)
        else:
            end_rate = float("nan")
        is_pc = bool((g["role"] == "positive_control").all())
        recovery = mean / pc_theoretical_nml_gvs if is_pc else float("nan")
        rows.append(
            {
                "experiment_id": exp_id,
                "substrate_id": sub,
                "role": "positive_control" if is_pc else "sample",
                "final_day": last_day,
                "final_yield_mean_nml_gvs": mean,
                "rsd_final": rsd,
                "end_daily_rate_frac": end_rate,
                "pc_recovery": recovery,
                "ok_rsd": bool(rsd <= rsd_max) if np.isfinite(rsd) else False,
                "ok_termination": (
                    bool(end_rate <= end_daily_rate_max) if np.isfinite(end_rate) else False
                ),
                "ok_pc": bool(pc_recovery_min <= recovery <= pc_recovery_max) if is_pc else None,
            }
        )
    return pd.DataFrame(rows)


def summarize_cstr(
    log: pd.DataFrame, period: str = "W", fos_tac_limit: float | None = None
) -> pd.DataFrame:
    """Reactor daily log → per-period means of OLR, HRT, specific yield and stability.

    Uses columns of ``templates/lab/cstr_daily_log_template.csv``. ``feed_vs_g`` may hold
    ``;``-separated values (co-digestion) which are summed. Outputs:

    - ``olr_gvs_l_d`` = Σ feed VS (g/d) / working volume (L)  (numerically = kg VS/m³·d)
    - ``hrt_d`` = working volume (L) / effluent volume (L/d)
    - ``ch4_nl_d`` = biogas (NL/d) × CH₄ %/100
    - ``spec_yield_nml_gvs`` = CH₄ (NmL/d) / feed VS (g/d)
    - ``fos_tac`` = FOS / TAC (both mg/L as reported) and ``ok_fos_tac`` if a limit is given
      (registry ``fos_tac_lim`` is K-flagged — pass it consciously).
    """
    df = log.copy()
    df = df[~df.get("notes", pd.Series("", index=df.index)).astype(str).str.contains("synthetic")]
    df["date"] = pd.to_datetime(df["date"])

    def _sum(v) -> float:
        if pd.isna(v) or v == "":
            return float("nan")
        return float(sum(float(x) for x in str(v).split(";") if x.strip()))

    df["feed_vs_total_g"] = df["feed_vs_g"].map(_sum)
    for c in ("working_volume_l", "effluent_volume_l", "biogas_nl", "ch4_pct", "fos_mg_l"):
        df[c] = pd.to_numeric(df[c], errors="coerce")
    df["tac_mg_caco3_l"] = pd.to_numeric(df["tac_mg_caco3_l"], errors="coerce")
    df["ch4_nl"] = df["biogas_nl"] * df["ch4_pct"] / 100.0
    grp = df.groupby(["reactor_id", pd.Grouper(key="date", freq=period)])
    out = grp.agg(
        days=("date", "count"),
        feed_vs_g_d=("feed_vs_total_g", "mean"),
        volume_l=("working_volume_l", "mean"),
        effluent_l_d=("effluent_volume_l", "mean"),
        ch4_nl_d=("ch4_nl", "mean"),
        fos_mg_l=("fos_mg_l", "mean"),
        tac_mg_l=("tac_mg_caco3_l", "mean"),
    ).reset_index()
    out["olr_gvs_l_d"] = out["feed_vs_g_d"] / out["volume_l"]
    out["hrt_d"] = out["volume_l"] / out["effluent_l_d"]
    out["spec_yield_nml_gvs"] = out["ch4_nl_d"] * 1000.0 / out["feed_vs_g_d"]
    out["fos_tac"] = out["fos_mg_l"] / out["tac_mg_l"]
    if fos_tac_limit is not None:
        out["ok_fos_tac"] = out["fos_tac"] <= fos_tac_limit
    return out


def proposed_registry_rows(
    param_id: str,
    module: str,
    name: str,
    values: np.ndarray | list[float],
    unit: str,
    experiment_id: str,
    lab: str,
    report_date: str,
) -> str:
    """Draft a ``parameters.csv`` line (central = mean, low/high = min/max of replicates).

    The row is flagged **V** because it comes from our own measured data; a human must still
    review conditions (temperature, inoculum, substrate origin), fill the evidence columns
    (``page`` = report table, ``quote``, ``verified_by``, ``verified_on``, ``conditions``; left
    empty here) and paste it in.
    """
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        raise ValueError("no finite values")
    source = f"CP2B {lab} {experiment_id} (internal report {report_date})"
    note = f"n={v.size} replicates; sd={v.std(ddof=1) if v.size > 1 else float('nan'):.3g}"
    return (
        f"{param_id},{module},{name},{v.mean():.4g},{v.min():.4g},{v.max():.4g},{unit},"
        f"{source},V,{note}" + "," * len(PARAMETER_EVIDENCE_COLUMNS)
    )
