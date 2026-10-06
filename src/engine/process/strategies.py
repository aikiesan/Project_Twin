"""Off-season strategies on the monthly residue table (docs/10 §3). v0: S0 and S1.

- **S0, vinasse only / no storage:** residues are fed in the month they are generated, so the
  digester idles off-season. This is the table :func:`engine.supply.residues.monthly_residues`
  already returns; nothing to apply.
- **S1, stored filter cake:** a share of the filter cake sent to AD is put in a silo during the
  harvest and released in the off-season months.

S1 storage is a single pool with a constant loss per month held (docs/12 Step 5 uses the same
balance)::

    I_open(t)  = I_close(t−1) · (1 − λ)
    out(t)     = (I_open(t) + in(t)) · w(t),   w(t) = share(t) / Σ_{u ≥ t} share(u)
    I_close(t) = I_open(t) + in(t) − out(t)

``w`` drains the pool by the last release month. The loss λ applies to the fresh mass (TS and
VS fall together), which is a v0 simplification: the registry's ``fc_storage_loss`` is a share of
the **methane potential** and is not numeric yet ("12 (4 mo) / 22 (6 mo)" %), so λ is an explicit
scenario input with its own source, never a default.

The off-season feed of an S1 plant is filter cake alone (TS ≈ 28 %), so the TS check of the
mass balance flags those months: a real plant dilutes with recirculated digestate, which v0 does
not model.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class StorageS1:
    """S1 settings.

    Attributes:
        store_frac: share of the filter cake to AD that goes to the silo in a storing month.
        store_months: calendar months in which cake is stored (normally the harvest months).
        release_months: calendar months in which the silo is emptied, in crop-year order.
        release_shares: relative release per release month (same length; default equal).
        loss_frac_per_month: fresh-mass loss per month held in the silo (λ above).
    """

    store_frac: float
    store_months: tuple[int, ...]
    release_months: tuple[int, ...]
    loss_frac_per_month: float
    release_shares: tuple[float, ...] | None = None

    def __post_init__(self) -> None:
        if not 0 <= self.store_frac <= 1:
            raise ValueError("store_frac must be a fraction in [0, 1]")
        if not 0 <= self.loss_frac_per_month < 1:
            raise ValueError("loss_frac_per_month must be in [0, 1)")
        for name in ("store_months", "release_months"):
            months = getattr(self, name)
            if not months or any(m not in range(1, 13) for m in months):
                raise ValueError(f"{name} must be calendar months 1-12")
            if len(set(months)) != len(months):
                raise ValueError(f"{name} has repeated months")
        if set(self.store_months) & set(self.release_months):
            raise ValueError("store_months and release_months must not overlap")
        if self.release_shares is not None:
            if len(self.release_shares) != len(self.release_months):
                raise ValueError("release_shares needs one share per release month")
            if any(s < 0 for s in self.release_shares) or sum(self.release_shares) <= 0:
                raise ValueError("release_shares must be >= 0 with a positive sum")


def apply_s1_storage(residues: pd.DataFrame, s1: StorageS1) -> pd.DataFrame:
    """Return a copy of the monthly residue table with S1 storage applied.

    ``filter_cake_to_ad_t_fm`` becomes the cake fed in each month (direct + released). New
    columns: ``filter_cake_stored_t_fm`` (into the silo), ``filter_cake_released_t_fm``,
    ``filter_cake_storage_loss_t_fm`` and ``filter_cake_stock_t_fm`` (closing stock). Months
    are processed in table order, which is crop-year order (April to March). Stock left at the
    end of the table is reported, not carried over.
    """
    if "filter_cake_to_ad_t_fm" not in residues.columns:
        raise ValueError("residues needs filter_cake_to_ad_t_fm (from monthly_residues)")
    out = residues.copy()
    cal = out["month"].str[5:7].astype(int).tolist()
    shares = s1.release_shares or tuple(1.0 for _ in s1.release_months)
    share_of = dict(zip(s1.release_months, shares, strict=True))
    release_order = [m for m in cal if m in share_of]

    stock = 0.0
    fed, stored, released, lost, stocks = [], [], [], [], []
    for m, cake in zip(cal, out["filter_cake_to_ad_t_fm"], strict=True):
        loss = stock * s1.loss_frac_per_month
        stock -= loss
        into = cake * s1.store_frac if m in s1.store_months else 0.0
        stock += into
        rel = 0.0
        if m in share_of:
            remaining = sum(share_of[u] for u in release_order[release_order.index(m) :])
            rel = stock * share_of[m] / remaining if remaining > 0 else 0.0
            stock -= rel
        fed.append(cake - into + rel)
        stored.append(into)
        released.append(rel)
        lost.append(loss)
        stocks.append(stock)
    out["filter_cake_stored_t_fm"] = stored
    out["filter_cake_released_t_fm"] = released
    out["filter_cake_storage_loss_t_fm"] = lost
    out["filter_cake_stock_t_fm"] = stocks
    out["filter_cake_to_ad_t_fm"] = fed
    return out


def storage_balance(table: pd.DataFrame) -> dict[str, float]:
    """Season totals of an S1 table: stored, released, lost and end stock (t FM)."""
    cols: Sequence[str] = (
        "filter_cake_stored_t_fm",
        "filter_cake_released_t_fm",
        "filter_cake_storage_loss_t_fm",
    )
    totals = {c: float(table[c].sum()) for c in cols}
    totals["filter_cake_end_stock_t_fm"] = float(table["filter_cake_stock_t_fm"].iloc[-1])
    return totals
