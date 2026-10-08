"""How concentrated a supply is across places: cumulative shares and counts to reach a share.

Used for the urban-residue ceiling (docs/12, ADR-0017 notes): if a few municipalities hold most
of the urban N3, the ceiling is reached with few plants.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
import pandas as pd


def cumulative_share(values: pd.Series) -> pd.DataFrame:
    """Sort descending; return ``value``, ``rank`` (1 = largest) and ``cum_share`` in [0, 1].

    NaN counts as 0. Raises ValueError when the total is not positive.
    """
    v = values.fillna(0.0).astype(float).sort_values(ascending=False)
    total = float(v.sum())
    if total <= 0:
        raise ValueError("total must be positive")
    return pd.DataFrame(
        {"value": v, "rank": np.arange(1, len(v) + 1), "cum_share": v.cumsum() / total},
        index=v.index,
    )


def count_for_share(values: pd.Series, shares: Sequence[float]) -> dict[float, int]:
    """Smallest number of places whose largest values reach each share of the total."""
    c = cumulative_share(values)["cum_share"].to_numpy()
    return {s: int(np.searchsorted(c, s - 1e-12) + 1) for s in shares}
