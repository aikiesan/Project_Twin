"""Extract the SEMIL-SP Anuário de Energéticos por Município 2025 (ano base 2024) tables.

Registry id ``semil_anuario_energeticos_2025``; parser in :mod:`engine.ingest.semil_anuario`.

Run (PYTHONPATH=src):
    python scripts/ingest/semil_anuario_2024.py <anuario.pdf> --names <ibge names: csv or shp>
        [--aliases aliases.csv] [--out data/interim/semil_anuario_2024]

Writes electricity.csv, natural_gas.csv, petroleum.csv (as printed, with pdf_page and
ibge_code), skipped_lines.csv, unmatched_names.csv, checks.json, and
energy_demand_municipal_2024.csv (one row per IBGE municipality; a municipality absent from the
gas table gets gas 0 and ``gas_listed=False``, one absent from another table gets NaN).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path

import pandas as pd

from engine.ingest.municipalities import read_names
from engine.ingest.pdftext import load_pages
from engine.ingest.semil_anuario import check_tables, match_ibge, parse_pages


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--names", type=Path, required=True)
    ap.add_argument(
        "--aliases",
        type=Path,
        default=Path(__file__).with_name("semil_anuario_aliases.csv"),
        help="CSV with columns pdf_name, ibge_name",
    )
    ap.add_argument("--out", type=Path, default=Path("data/interim/semil_anuario_2024"))
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)

    sha = hashlib.sha256(a.pdf.read_bytes()).hexdigest()
    pages = load_pages(a.pdf)
    tables = parse_pages(pages)
    ibge = read_names(a.names)
    aliases = {}
    if a.aliases:
        al = pd.read_csv(a.aliases, dtype=str)
        aliases = dict(zip(al["pdf_name"], al["ibge_name"], strict=True))

    unmatched, merged = [], ibge.set_index("ibge_code")[["name"]]
    for key in ("electricity", "natural_gas", "petroleum"):
        df = tables[key]
        df.insert(1, "ibge_code", match_ibge(df["municipio_pdf"], ibge, aliases))
        df.to_csv(a.out / f"{key}.csv", index=False)
        body = df[~df["is_total"]]
        miss = body[body["ibge_code"].isna()]
        unmatched += [{"section": key, "municipio_pdf": n} for n in miss["municipio_pdf"]]
        vals = body.dropna(subset=["ibge_code"]).drop_duplicates("ibge_code")
        vals = vals.drop(columns=["municipio_pdf", "pdf_page", "is_total"]).set_index("ibge_code")
        merged = merged.join(vals)
    gas_cols = [c for c in merged.columns if c.startswith("gas_")]
    merged["gas_listed"] = merged[gas_cols].notna().any(axis=1)
    merged[gas_cols] = merged[gas_cols].fillna(0)
    merged.reset_index().to_csv(a.out / "energy_demand_municipal_2024.csv", index=False)

    tables["skipped"].to_csv(a.out / "skipped_lines.csv", index=False)
    pd.DataFrame(unmatched, columns=["section", "municipio_pdf"]).to_csv(
        a.out / "unmatched_names.csv", index=False
    )
    checks = {
        "pdf": a.pdf.name,
        "sha256": sha,
        "pdf_pages": len(pages),
        "ibge_municipalities": int(len(ibge)),
        "unmatched": len(unmatched),
        "tables": check_tables(tables),
    }
    (a.out / "checks.json").write_text(json.dumps(checks, indent=2, ensure_ascii=False))
    print(json.dumps(checks, indent=2, ensure_ascii=False))
    if unmatched:
        names = sorted({u["municipio_pdf"] for u in unmatched})
        print(f"{len(names)} unmatched names (first 40):", names[:40])


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")  # names with accents survive "> file" on Windows
    main()
