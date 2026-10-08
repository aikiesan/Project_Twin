"""SP municipality names keyed on the IBGE 7-digit code, from any table the project already holds.

Accepts a CSV (e.g. ``municipal_panel_v0.csv``: ``ibge_code``, ``municipality_name``) or a vector
file (IBGE mesh: ``CD_MUN``, ``NM_MUN``; read without geometry). Codes come back as ``int`` so
they join with tables where ``ibge_code`` is text (``"3554508"``) after the same conversion.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

CODE_COLS = ("ibge_code", "CD_MUN", "cd_mun", "cod_ibge", "codigo_ibge")
NAME_COLS = (
    "name",
    "municipality_name",
    "NM_MUN",
    "nm_mun",
    "nome",
    "municipio",
    "name_municipality",
)


def read_names(path: Path) -> pd.DataFrame:
    """``ibge_code`` (int, SP only) and ``name``, one row per municipality.

    Raises:
        KeyError: no code or no name column among :data:`CODE_COLS` / :data:`NAME_COLS`.
    """
    path = Path(path)
    if path.suffix.lower() == ".csv":
        df = pd.read_csv(path, dtype=str)
    else:
        import pyogrio  # optional: only for shapefile / GeoPackage input

        df = pyogrio.read_dataframe(path, read_geometry=False)
    code = next((c for c in CODE_COLS if c in df.columns), None)
    name = next((c for c in NAME_COLS if c in df.columns), None)
    if code is None or name is None:
        raise KeyError(
            f"{path.name}: needs a code column ({', '.join(CODE_COLS)}) and a name column "
            f"({', '.join(NAME_COLS)}); found {list(df.columns)}"
        )
    out = pd.DataFrame({"ibge_code": df[code].astype(str).str[:7].astype(int), "name": df[name]})
    return out[out["ibge_code"].between(3500000, 3599999)].drop_duplicates("ibge_code")


def name_map(path: Path) -> dict[int, str]:
    """``{ibge_code: name}`` for joining onto result tables."""
    t = read_names(path)
    return dict(zip(t["ibge_code"], t["name"], strict=True))
