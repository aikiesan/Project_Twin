"""Build the local project viewer: datasets, map layers, project flow and progress.

Everything is read from the repository and ``data/``; nothing is fetched from the network.
The output is a static folder (default ``exports/viewer/``, gitignored)::

    index.html     single-page app (Leaflet map + tables), copied from this package
    data.json      registry, roadmap, ADRs, modules, git history, layer index
    layers/*.geojson  simplified layers in EPSG:4326 (coordinates rounded to ~1 m)

Layers marked ``private: true`` in ``layers.yaml`` come from ``data/private/``; pass
``include_private=False`` for any build that leaves this PC (CLAUDE.md rule 6).
"""

from __future__ import annotations

import csv
import json
import re
import shutil
import subprocess
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

import yaml

PACKAGE_DIR = Path(__file__).parent

#: Project flow in pipeline order: (id, title, engine sub-package, method doc, registry modules).
FLOW = (
    ("ingest", "Data & registry", "ingest", "08_VERIFICATION_PROTOCOL.md", ()),
    ("supply", "Supply", "supply", "09_MODULE_SUPPLY.md", ("supply", "environment")),
    ("process", "Process", "process", "10_MODULE_PROCESS.md", ("process",)),
    (
        "economics",
        "Economics",
        "economics",
        "11_MODULE_ECONOMICS.md",
        ("costs", "market", "regulation", "intl_benchmark"),
    ),
    (
        "siting",
        "Siting & logistics",
        "siting",
        "12_MODULE_SITING_LOGISTICS.md",
        ("siting", "spatial"),
    ),
    ("calibrate", "Calibration", "calibrate", "13_MODULE_CALIBRATION_VALIDATION.md", ()),
    ("export", "Export to PILAR-2b", "export", "18_PILAR2B_INTEGRATION.md", ()),
)

_CHECKBOX = re.compile(r"^\s*- \[( |x|X)\] (.*)$")
_ADR_ROW = re.compile(r"^\| \[(\d{4})\]\(([^)]+)\) \| (.+?) \| (.+?) \|\s*$")


@dataclass
class Layer:
    """One entry of ``layers.yaml`` after it was built."""

    id: str
    title: str
    group: str
    source_id: str
    kind: str
    file: str
    n_features: int
    private: bool
    style: dict


# --------------------------------------------------------------------------------------
# text parsers (pure functions, unit-tested)
# --------------------------------------------------------------------------------------
def parse_roadmap(md: str) -> list[dict]:
    """Phases (``## ``) → sections (``### ``) → checklist items from docs/19.

    Returns ``[{"title", "sections": [{"title", "items": [{"text", "done"}]}]}]``. Items placed
    directly under a phase go into a section with an empty title.
    """
    phases: list[dict] = []
    for line in md.splitlines():
        if line.startswith("## "):
            phases.append({"title": line[3:].strip(), "sections": []})
        elif line.startswith("### ") and phases:
            phases[-1]["sections"].append({"title": line[4:].strip(), "items": []})
        else:
            m = _CHECKBOX.match(line)
            if m and phases:
                if not phases[-1]["sections"]:
                    phases[-1]["sections"].append({"title": "", "items": []})
                phases[-1]["sections"][-1]["items"].append(
                    {"text": m.group(2).strip(), "done": m.group(1).lower() == "x"}
                )
    return [p for p in phases if any(s["items"] for s in p["sections"])]


def parse_adrs(md: str) -> list[dict]:
    """ADR rows from the ``docs/decisions/README.md`` table."""
    out = []
    for line in md.splitlines():
        m = _ADR_ROW.match(line)
        if m:
            out.append(
                {"num": m.group(1), "file": m.group(2), "title": m.group(3), "status": m.group(4)}
            )
    return out


def folder_stats(path: Path) -> tuple[int, int]:
    """``(n_files, bytes)`` under ``path`` (0, 0 if it does not exist)."""
    if not path.exists():
        return 0, 0
    files = [p for p in path.rglob("*") if p.is_file()] if path.is_dir() else [path]
    return len(files), sum(p.stat().st_size for p in files)


def summarize_sources(entries: list[dict], repo: Path) -> list[dict]:
    """Registry entries reduced to what the viewer shows, plus on-disk presence and size."""
    out = []
    for e in entries:
        local = str(e.get("local_path") or "")
        on_disk = local.startswith("data/")
        n_files, size = folder_stats(repo / local) if on_disk else (0, 0)
        out.append(
            {
                "id": e.get("id"),
                "name": e.get("name", ""),
                "publisher": e.get("publisher", ""),
                "module": e.get("module", ""),
                "status": e.get("status", ""),
                "confidence": e.get("confidence", ""),
                "access": e.get("access", ""),
                "license": str(e.get("license", "")),
                "url": str(e.get("url", "")),
                "local_path": local,
                "accessed": str(e.get("accessed", "")),
                "spatial": str(e.get("spatial", "")),
                "temporal": str(e.get("temporal", "")),
                "format": str(e.get("format", "")),
                "notes": " ".join(str(e.get("notes", "")).split()),
                "private": local.startswith("data/private/"),
                "on_disk": n_files > 0,
                "n_files": n_files,
                "size_bytes": size,
            }
        )
    return out


def count_by(rows: list[dict], key: str) -> dict[str, int]:
    """Frequency of ``row[key]`` values, most common first."""
    counts: dict[str, int] = {}
    for r in rows:
        k = str(r.get(key) or "—")
        counts[k] = counts.get(k, 0) + 1
    return dict(sorted(counts.items(), key=lambda kv: -kv[1]))


# --------------------------------------------------------------------------------------
# repository readers
# --------------------------------------------------------------------------------------
def _git(repo: Path, *args: str) -> str:
    try:
        return subprocess.run(
            ["git", *args], cwd=repo, capture_output=True, text=True, check=True, encoding="utf-8"
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return ""


def git_history(repo: Path, n: int = 60) -> list[dict]:
    """Last ``n`` commits on HEAD (first-parent, so merged PRs show as one line)."""
    out = []
    raw = _git(repo, "log", "--first-parent", f"-{n}", "--date=short", "--format=%h%x1f%ad%x1f%s")
    for line in raw.splitlines():
        parts = line.split("\x1f")
        if len(parts) == 3:
            out.append({"hash": parts[0], "date": parts[1], "subject": parts[2]})
    return out


def pull_requests(repo: Path) -> list[dict]:
    """PRs of the GitHub repo via the ``gh`` CLI; empty when ``gh`` is missing or offline."""
    try:
        res = subprocess.run(
            [
                "gh",
                "pr",
                "list",
                "--state",
                "all",
                "--limit",
                "50",
                "--json",
                "number,title,state,createdAt,mergedAt,url,headRefName",
            ],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=20,
        )
        return json.loads(res.stdout) if res.returncode == 0 and res.stdout.strip() else []
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError):
        return []


def module_status(repo: Path, sources: list[dict]) -> list[dict]:
    """One card per pipeline step: code files, tests, method doc and registry coverage."""
    tests = sorted(p.name for p in (repo / "tests").glob("test_*.py"))
    out = []
    for fid, title, pkg, doc, reg_modules in FLOW:
        code = sorted(
            p.name for p in (repo / "src" / "engine" / pkg).glob("*.py") if p.name != "__init__.py"
        )
        stems = [c.removesuffix(".py") for c in code if c != "__main__.py"]
        mod_tests = [t for t in tests if any(s in t for s in [*stems, pkg])]
        regs = sources if fid == "ingest" else [s for s in sources if s["module"] in reg_modules]
        out.append(
            {
                "id": fid,
                "title": title,
                "code": code,
                "tests": mod_tests,
                "doc": doc if (repo / "docs" / doc).exists() else "",
                "registry_modules": list(reg_modules),
                "n_sources": len(regs),
                "n_have": sum(1 for s in regs if s["status"] == "have"),
                "n_verified": sum(1 for s in regs if s["confidence"] == "V"),
            }
        )
    return out


def parameters_summary(repo: Path) -> dict:
    """Counts of ``registry/parameters.csv`` by confidence flag and module."""
    path = repo / "registry" / "parameters.csv"
    if not path.exists():
        return {"n": 0, "by_confidence": {}, "by_module": {}}
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    return {
        "n": len(rows),
        "by_confidence": count_by(rows, "confidence"),
        "by_module": count_by(rows, "module"),
    }


# --------------------------------------------------------------------------------------
# map layers (geopandas imported lazily: the rest of the viewer works without the geo extra)
# --------------------------------------------------------------------------------------
def _round(gdf, digits: int = 5):
    import shapely

    gdf = gdf.copy()
    geoms = shapely.force_2d(gdf.geometry.values)
    gdf["geometry"] = shapely.set_precision(geoms, 10**-digits)
    return gdf[~(gdf.geometry.is_empty | gdf.geometry.isna())]


def _clean_props(gdf, max_cols: int = 12):
    import pandas as pd

    keep = [c for c in gdf.columns if c != "geometry"][:max_cols]
    out = gdf[keep + ["geometry"]].copy()
    for c in keep:
        if pd.api.types.is_datetime64_any_dtype(out[c]):
            out[c] = out[c].astype(str)
        elif out[c].dtype == object:
            out[c] = out[c].map(
                lambda v: v if v is None or isinstance(v, str | int | float) else str(v)
            )
    return out


def _read_vector(repo: Path, path: str, encoding: str | None = None):
    import geopandas as gpd

    full = path if path.startswith("/vsizip/") else str(repo / path)
    if full.startswith("/vsizip/"):
        full = "/vsizip/" + str(repo / full.removeprefix("/vsizip/"))
    kwargs = {"encoding": encoding} if encoding else {}
    return gpd.read_file(full, **kwargs)


def build_layer(spec: dict, repo: Path, sp_geom, out_dir: Path) -> Layer:
    """Read, reproject to EPSG:4326, clip/simplify and write one layer as GeoJSON."""
    import geopandas as gpd
    import pandas as pd

    kind = spec["kind"]
    if kind == "points":
        df = pd.read_csv(repo / spec["path"], sep=spec.get("sep", ","), encoding="utf-8-sig")
        for col, val in (spec.get("filter") or {}).items():
            df = df[df[col].astype(str) == str(val)]
        gdf = gpd.GeoDataFrame(
            df,
            geometry=gpd.points_from_xy(
                pd.to_numeric(df[spec["lon"]]), pd.to_numeric(df[spec["lat"]])
            ),
            crs="EPSG:4326",
        )
    elif kind == "choropleth":
        gdf = _read_vector(repo, spec["geometry"], spec.get("encoding"))
        if spec.get("table"):
            tab = pd.read_csv(repo / spec["table"], encoding="utf-8-sig")
            gdf[spec["geometry_key"]] = gdf[spec["geometry_key"]].astype(str)
            tab[spec["table_key"]] = tab[spec["table_key"]].astype(str)
            cols = [spec["table_key"], spec["value"]] + (
                [spec["label"]] if spec.get("label") in tab.columns else []
            )
            gdf = gdf.merge(tab[cols], left_on=spec["geometry_key"], right_on=spec["table_key"])
        gdf = gdf[[c for c in (spec.get("label"), spec["value"]) if c] + ["geometry"]]
    else:
        gdf = _read_vector(repo, spec["path"], spec.get("encoding"))

    if gdf.crs is None:
        raise ValueError(f"{spec['id']}: layer has no CRS")
    gdf = gdf.to_crs("EPSG:4326")
    if spec.get("clip_sp") and sp_geom is not None:
        gdf = gdf[gdf.intersects(sp_geom)]
    if spec.get("simplify"):
        gdf["geometry"] = gdf.geometry.simplify(float(spec["simplify"]), preserve_topology=True)
    gdf = _clean_props(_round(gdf))

    style = {
        k: spec[k] for k in ("color", "weight", "value", "label", "unit", "visible") if k in spec
    }
    if kind == "choropleth":
        vals = pd.to_numeric(gdf[spec["value"]], errors="coerce").dropna()
        qs = (0.2, 0.4, 0.6, 0.8)
        style["breaks"] = [float(vals.quantile(q)) for q in qs] if len(vals) else []
        style["min"], style["max"] = (float(vals.min()), float(vals.max())) if len(vals) else (0, 0)

    out_dir.mkdir(parents=True, exist_ok=True)
    fname = f"{spec['id']}.geojson"
    (out_dir / fname).write_text(gdf.to_json(drop_id=True), encoding="utf-8")
    return Layer(
        id=spec["id"],
        title=spec["title"],
        group=spec.get("group", "Other"),
        source_id=spec["source_id"],
        kind="polygon-value" if kind == "choropleth" else kind,
        file=f"layers/{fname}",
        n_features=len(gdf),
        private=bool(spec.get("private")),
        style=style,
    )


def build_layers(
    cfg: dict, repo: Path, out_dir: Path, *, include_private: bool, known_ids: set[str]
) -> tuple[list[Layer], list[str]]:
    """Build every layer in ``cfg``; returns layers and human-readable problems (never raises)."""
    import geopandas as gpd

    problems: list[str] = []
    sp_geom = None
    try:
        sp = gpd.read_file(repo / cfg["sp_boundary"]).to_crs("EPSG:4326")
        sp_geom = sp.union_all().buffer(0.01)
        (out_dir).mkdir(parents=True, exist_ok=True)
        outline = sp[["geometry"]].copy()
        outline["geometry"] = outline.geometry.simplify(0.0005, preserve_topology=True)
        (out_dir / "sp_boundary.geojson").write_text(
            _round(outline).to_json(drop_id=True), encoding="utf-8"
        )
    except Exception as exc:  # noqa: BLE001 - viewer must still build
        problems.append(f"SP boundary: {exc}")

    layers: list[Layer] = []
    for spec in cfg.get("layers", []):
        if spec.get("private") and not include_private:
            continue
        if spec["source_id"] not in known_ids:
            problems.append(f"{spec['id']}: source_id {spec['source_id']!r} is not in the registry")
            continue
        try:
            layers.append(build_layer(spec, repo, sp_geom, out_dir))
        except Exception as exc:  # noqa: BLE001 - one bad layer must not stop the others
            problems.append(f"{spec['id']}: {type(exc).__name__}: {exc}")
    return layers, problems


# --------------------------------------------------------------------------------------
# entry point
# --------------------------------------------------------------------------------------
def build(
    repo: Path,
    out: Path,
    *,
    include_private: bool = True,
    with_layers: bool = True,
    with_prs: bool = True,
) -> dict:
    """Write ``index.html``, ``data.json`` and ``layers/`` to ``out``; returns the data dict."""
    repo = repo.resolve()
    out.mkdir(parents=True, exist_ok=True)
    entries = yaml.safe_load((repo / "registry" / "sources.yaml").read_text(encoding="utf-8"))
    entries = entries.get("sources", entries) if isinstance(entries, dict) else entries
    sources = summarize_sources(entries, repo)

    layers: list[Layer] = []
    problems: list[str] = []
    if with_layers:
        layer_dir = out / "layers"
        if layer_dir.exists():
            shutil.rmtree(layer_dir)
        cfg = yaml.safe_load((PACKAGE_DIR / "layers.yaml").read_text(encoding="utf-8"))
        layers, problems = build_layers(
            cfg,
            repo,
            layer_dir,
            include_private=include_private,
            known_ids={s["id"] for s in sources},
        )

    roadmap_md = repo / "docs" / "19_ROADMAP_STEP_BY_STEP.md"
    adr_md = repo / "docs" / "decisions" / "README.md"
    data = {
        "generated_at": datetime.now(tz=UTC).strftime("%Y-%m-%d %H:%M UTC"),
        "git": {
            "branch": _git(repo, "rev-parse", "--abbrev-ref", "HEAD").strip(),
            "commit": _git(repo, "rev-parse", "--short", "HEAD").strip(),
        },
        "include_private": include_private,
        "sources": sources,
        "source_counts": {
            "status": count_by(sources, "status"),
            "confidence": count_by(sources, "confidence"),
            "module": count_by(sources, "module"),
            "access": count_by(sources, "access"),
        },
        "data_on_disk": {
            "n_files": sum(s["n_files"] for s in sources),
            "size_bytes": sum(s["size_bytes"] for s in sources),
        },
        "parameters": parameters_summary(repo),
        "modules": module_status(repo, sources),
        "roadmap": (
            parse_roadmap(roadmap_md.read_text(encoding="utf-8")) if roadmap_md.exists() else []
        ),
        "adrs": parse_adrs(adr_md.read_text(encoding="utf-8")) if adr_md.exists() else [],
        "commits": git_history(repo),
        "pull_requests": pull_requests(repo) if with_prs else [],
        "layers": [layer.__dict__ for layer in layers],
        "layer_problems": problems,
    }
    (out / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    shutil.copyfile(PACKAGE_DIR / "index.html", out / "index.html")
    return data
