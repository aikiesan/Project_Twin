import json

from engine.viz.build import build, count_by, parse_adrs, parse_roadmap, summarize_sources

ROADMAP = """# 19 — Roadmap
intro
## PHASE 0 — Foundation
### Week 1
- [x] Create repo
- [ ] Restore dump
## PHASE 1 — Supply
- [ ] Facilities registry
## Notes without items
text only
"""

ADRS = """| ADR | Title | Status |
|---|---|---|
| [0001](ADR-0001-a.md) | First decision | Accepted |
| [0002](ADR-0002-b.md) | Second one | Proposed |
"""


def test_parse_roadmap_phases_sections_items():
    phases = parse_roadmap(ROADMAP)
    assert [p["title"] for p in phases] == ["PHASE 0 — Foundation", "PHASE 1 — Supply"]
    week1 = phases[0]["sections"][0]
    assert week1["title"] == "Week 1"
    assert [(i["text"], i["done"]) for i in week1["items"]] == [
        ("Create repo", True),
        ("Restore dump", False),
    ]
    # items directly under a phase get an untitled section
    assert phases[1]["sections"][0]["title"] == ""


def test_parse_adrs():
    adrs = parse_adrs(ADRS)
    assert [(a["num"], a["status"]) for a in adrs] == [("0001", "Accepted"), ("0002", "Proposed")]
    assert adrs[0]["file"] == "ADR-0001-a.md"


def test_summarize_sources_disk_presence_and_private(tmp_path):
    (tmp_path / "data" / "raw" / "a").mkdir(parents=True)
    (tmp_path / "data" / "raw" / "a" / "f.csv").write_bytes(b"x,1\n")
    (tmp_path / "data" / "private" / "p").mkdir(parents=True)
    (tmp_path / "data" / "private" / "p" / "g.csv").write_text("y\n")
    rows = summarize_sources(
        [
            {"id": "a", "local_path": "data/raw/a/", "status": "have", "confidence": "V"},
            {"id": "p", "local_path": "data/private/p/", "status": "have"},
            {"id": "u", "url": "https://example.org", "status": "get"},
        ],
        tmp_path,
    )
    by = {r["id"]: r for r in rows}
    assert by["a"]["on_disk"] and by["a"]["n_files"] == 1 and by["a"]["size_bytes"] == 4
    assert by["p"]["private"] and not by["a"]["private"]
    assert not by["u"]["on_disk"]
    assert count_by(rows, "status") == {"have": 2, "get": 1}


def test_build_without_layers_writes_page_and_json(tmp_path):
    repo = tmp_path / "repo"
    (repo / "registry").mkdir(parents=True)
    (repo / "registry" / "sources.yaml").write_text(
        "sources:\n  - id: a\n    module: supply\n    status: have\n    confidence: V\n",
        encoding="utf-8",
    )
    (repo / "docs" / "decisions").mkdir(parents=True)
    (repo / "docs" / "19_ROADMAP_STEP_BY_STEP.md").write_text(ROADMAP, encoding="utf-8")
    (repo / "docs" / "decisions" / "README.md").write_text(ADRS, encoding="utf-8")
    out = tmp_path / "viewer"
    data = build(repo, out, with_layers=False, with_prs=False)
    assert (out / "index.html").exists()
    saved = json.loads((out / "data.json").read_text(encoding="utf-8"))
    assert saved["sources"][0]["id"] == "a"
    assert data["modules"][1]["id"] == "supply" and data["modules"][1]["n_sources"] == 1
    assert len(saved["roadmap"]) == 2 and len(saved["adrs"]) == 2
    assert saved["layers"] == []
