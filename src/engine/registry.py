"""Access to the in-git registry: ``parameters.csv``, ``sources.yaml``, ``projects_capex.csv``.

This module is the **single entry point** other modules use to read model parameters, so every
number used in a run can be traced to a registry row (id, source, confidence flag).

Public API (stable — other modules depend on it):

- :func:`load_parameters` -> ``dict[str, Param]``
- :func:`get_param` -> :class:`Param`
- :func:`load_sources` -> ``list[dict]``
- :func:`load_projects_capex` -> ``pandas.DataFrame``

Parameters whose ``central`` field is not a single number (e.g. ``"16 / 9"`` for TS / VS)
keep the raw text in :attr:`Param.raw_central` and have ``central = None``.
"""

from __future__ import annotations

import csv
import math
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from engine import REGISTRY_DIR

PARAMETERS_CSV = REGISTRY_DIR / "parameters.csv"
SOURCES_YAML = REGISTRY_DIR / "sources.yaml"
PROJECTS_CAPEX_CSV = REGISTRY_DIR / "projects_capex.csv"

CONFIDENCE_FLAGS = ("V", "S", "K", "D")


def _to_float(text: str | None) -> float | None:
    """Parse a registry cell to float; return ``None`` for blanks or non-numeric text."""
    if text is None:
        return None
    text = text.strip()
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


@dataclass(frozen=True)
class Param:
    """One row of ``registry/parameters.csv``.

    Attributes:
        id: unique parameter id (e.g. ``"vin_gen"``).
        module: owning module (supply, process, costs, market, spatial).
        name: human-readable parameter name.
        central, low, high: numeric values in ``unit`` (``None`` when blank/non-numeric).
        unit: unit string exactly as in the registry.
        source: citation text.
        confidence: one of V, S, K, D (see docs/08_VERIFICATION_PROTOCOL.md).
        notes: free text.
        raw_central, raw_low, raw_high: the original cell text.
    """

    id: str
    module: str
    name: str
    central: float | None
    low: float | None
    high: float | None
    unit: str
    source: str
    confidence: str
    notes: str
    raw_central: str
    raw_low: str
    raw_high: str

    @property
    def has_range(self) -> bool:
        """True when both ``low`` and ``high`` are numeric."""
        return self.low is not None and self.high is not None

    def require_central(self) -> float:
        """Return ``central`` or raise if the registry has no numeric central value."""
        if self.central is None:
            raise ValueError(
                f"Parameter {self.id!r} has no numeric central value "
                f"(raw={self.raw_central!r}); pass the value explicitly."
            )
        return self.central


@lru_cache(maxsize=8)
def _load_parameters_cached(path: str) -> tuple[Param, ...]:
    rows: list[Param] = []
    with open(path, newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            rows.append(
                Param(
                    id=row["id"].strip(),
                    module=(row.get("module") or "").strip(),
                    name=(row.get("parameter") or "").strip(),
                    central=_to_float(row.get("central")),
                    low=_to_float(row.get("low")),
                    high=_to_float(row.get("high")),
                    unit=(row.get("unit") or "").strip(),
                    source=(row.get("source") or "").strip(),
                    confidence=(row.get("confidence") or "").strip(),
                    notes=(row.get("notes") or "").strip(),
                    raw_central=(row.get("central") or "").strip(),
                    raw_low=(row.get("low") or "").strip(),
                    raw_high=(row.get("high") or "").strip(),
                )
            )
    return tuple(rows)


def load_parameters(path: Path | str = PARAMETERS_CSV) -> dict[str, Param]:
    """Load ``parameters.csv`` into ``{id: Param}`` (cached per path)."""
    return {p.id: p for p in _load_parameters_cached(str(path))}


def get_param(param_id: str, path: Path | str = PARAMETERS_CSV) -> Param:
    """Return one parameter by id; raise ``KeyError`` with a helpful message if absent."""
    params = load_parameters(path)
    if param_id not in params:
        raise KeyError(
            f"Parameter {param_id!r} is not in {path}. Add it to the registry (with source and "
            "confidence flag) instead of hard-coding a value."
        )
    return params[param_id]


def load_sources(path: Path | str = SOURCES_YAML) -> list[dict]:
    """Return the list under ``sources:`` in ``sources.yaml``."""
    with open(path, encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    return list(doc.get("sources", []))


def load_projects_capex(path: Path | str = PROJECTS_CAPEX_CSV):
    """Return ``projects_capex.csv`` as a pandas DataFrame (numeric columns coerced)."""
    import pandas as pd

    df = pd.read_csv(path, dtype=str, keep_default_na=False)
    for col in ("capacity_value", "investment_total_R$M", "bndes_R$M"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.replace(",", "", regex=False), errors="coerce")
    return df
