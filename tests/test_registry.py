"""Tests for registry validation, summary, parameter hash and CLI (engine.registry).

All fixture rows below are SYNTHETIC (made-up ids/values written to tmp_path); they are not
registry data. Only the ``test_real_registry_*`` tests read the real files in ``registry/``.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from engine import registry as reg
from engine.registry import (
    Issue,
    Param,
    load_parameters,
    main,
    param_hash,
    summary_markdown,
    validate_all,
    validate_parameters,
    validate_projects_capex,
    validate_sources,
)

PARAM_HEADER = "id,module,parameter,central,low,high,unit,source,confidence,notes\n"
# SYNTHETIC parameter rows (values are arbitrary test numbers).
PARAM_ROWS_OK = (
    "syn_a,process,Synthetic A,2,1,3,kg per t,Synthetic fixture,S,\n"
    "syn_b,supply,Synthetic B,0.5,,,fraction,Synthetic fixture,D,\n"
)

SOURCES_OK = """\
schema_version: 0.1
updated: 2026-10-04
sources:
  - id: syn_source
    name: Synthetic source
    publisher: Synthetic publisher
    url: https://example.org/synthetic
    module: supply
    status: get
    confidence: S   # trailing YAML comment is ignored
    access: open
    license: synthetic
"""

PROJECTS_HEADER = (
    "id,project,location,uf,feedstock,capacity_value,capacity_unit,capacity_basis,"
    "investment_total_R$M,bndes_R$M,year,status,source,confidence,notes\n"
)
# SYNTHETIC project row.
PROJECT_ROW_OK = (
    "1,Synthetic plant,Nowhere,SP,vinasse,1000,Nm3/d,nominal,10,5,2026,planned,syn,S,\n"
)


def _write(path: Path, text: str | bytes) -> Path:
    if isinstance(text, bytes):
        path.write_bytes(text)
    else:
        path.write_text(text, encoding="utf-8")
    return path


def _levels(issues: list[Issue]) -> tuple[list[Issue], list[Issue]]:
    return (
        [i for i in issues if i.level == "error"],
        [i for i in issues if i.level == "warning"],
    )


@pytest.fixture
def clean_registry(tmp_path: Path) -> Path:
    """A synthetic registry folder with no errors and no warnings."""
    folder = tmp_path / "registry"
    folder.mkdir()
    _write(folder / "parameters.csv", PARAM_HEADER + PARAM_ROWS_OK)
    _write(folder / "sources.yaml", SOURCES_OK)
    _write(folder / "projects_capex.csv", PROJECTS_HEADER + PROJECT_ROW_OK)
    return folder


# ---------------------------------------------------------------------------------------------
# parameters.csv
# ---------------------------------------------------------------------------------------------


def test_parameters_clean_file_has_no_issues(tmp_path: Path) -> None:
    path = _write(tmp_path / "parameters.csv", PARAM_HEADER + PARAM_ROWS_OK)
    assert validate_parameters(path) == []


def test_parameters_ids_unique_nonempty_snake_case(tmp_path: Path) -> None:
    rows = (
        "syn_a,process,A,2,1,3,-,syn,S,\n"  # line 2
        "syn_a,process,A again,2,1,3,-,syn,S,\n"  # line 3: duplicate
        ",process,No id,2,1,3,-,syn,S,\n"  # line 4: empty id
        "SynCamel,process,Camel,2,1,3,-,syn,S,\n"  # line 5: not snake_case
    )
    errors, _ = _levels(validate_parameters(_write(tmp_path / "p.csv", PARAM_HEADER + rows)))
    by_line = {e.row: e for e in errors}
    assert set(by_line) == {3, 4, 5}
    assert by_line[3].id == "syn_a" and "first defined on line 2" in by_line[3].message
    assert by_line[4].message == "empty id"
    assert "not snake_case" in by_line[5].message


@pytest.mark.parametrize("flag", ["X", "S/D", "v", ""])
def test_parameters_confidence_must_be_single_valid_flag(tmp_path: Path, flag: str) -> None:
    path = _write(tmp_path / "p.csv", PARAM_HEADER + f"syn_a,process,A,2,1,3,-,syn,{flag},\n")
    errors, _ = _levels(validate_parameters(path))
    assert len(errors) == 1 and "confidence" in errors[0].message


def test_parameters_unit_and_source_required(tmp_path: Path) -> None:
    rows = "syn_a,process,A,2,1,3,,syn,S,\nsyn_b,process,B,2,1,3,-,,S,\n"
    errors, _ = _levels(validate_parameters(_write(tmp_path / "p.csv", PARAM_HEADER + rows)))
    assert [(e.id, e.message.split(" ")[0]) for e in errors] == [
        ("syn_a", "unit"),
        ("syn_b", "source"),
    ]


def test_parameters_numeric_ordering(tmp_path: Path) -> None:
    rows = (
        # all numeric, low=3 > central=2 -> error (3 <= 2 is false)
        "syn_bad,process,Bad,2,3,4,-,syn,S,\n"
        # equal values are ordered: 2 <= 2 <= 2 -> ok
        "syn_eq,process,Equal,2,2,2,-,syn,S,\n"
        # only low/high numeric, 1 <= 3 -> ok (central blank -> warning only)
        "syn_range,process,Range,,1,3,-,syn,S,\n"
        # only central/high numeric but central=5 > high=3 -> error (pairwise check)
        "syn_pair,process,Pair,5,,3,-,syn,S,\n"
    )
    issues = validate_parameters(_write(tmp_path / "p.csv", PARAM_HEADER + rows))
    errors, warns = _levels(issues)
    assert sorted(e.id for e in errors) == ["syn_bad", "syn_pair"]
    bad = next(e for e in errors if e.id == "syn_bad")
    assert "low > central" in bad.message and "low=3, central=2, high=4" in bad.message
    assert "central > high" in next(e for e in errors if e.id == "syn_pair").message
    assert [w.id for w in warns] == ["syn_range"]
    assert "central is blank" in warns[0].message


def test_parameters_non_numeric_central_is_warning(tmp_path: Path) -> None:
    rows = "syn_ts_vs,process,TS / VS,16 / 9,15-50 / 8-35,,g/L,syn,S,\n"
    errors, warns = _levels(validate_parameters(_write(tmp_path / "p.csv", PARAM_HEADER + rows)))
    assert errors == []
    assert [w.message for w in warns] == [
        "non-numeric central '16 / 9': kept as Param.raw_central, Param.central is None",
        "non-numeric low '15-50 / 8-35': kept as Param.raw_low, Param.low is None",
    ]


def test_parameters_structural_errors(tmp_path: Path) -> None:
    # missing column 'notes'
    no_notes = "id,module,parameter,central,low,high,unit,source,confidence\n"
    issues = validate_parameters(_write(tmp_path / "a.csv", no_notes + "syn_a,p,A,1,,,-,s,S\n"))
    assert [i.message for i in issues] == ["missing required column(s): notes"]
    # unquoted comma -> one extra field; truncated row -> fewer fields
    rows = "syn_a,process,A,2,1,3,-,syn, with comma,S,\nsyn_b,process,B,2\n"
    errors, _ = _levels(validate_parameters(_write(tmp_path / "b.csv", PARAM_HEADER + rows)))
    assert "1 more field(s)" in errors[0].message and errors[0].row == 2
    assert errors[1].message == "row has fewer fields than the header" and errors[1].row == 3
    # BOM -> error (the loader would then fail on '﻿id')
    bom = b"\xef\xbb\xbf" + (PARAM_HEADER + PARAM_ROWS_OK).encode()
    errors, _ = _levels(validate_parameters(_write(tmp_path / "c.csv", bom)))
    assert len(errors) == 1 and "byte-order mark" in errors[0].message
    # missing file
    errors, _ = _levels(validate_parameters(tmp_path / "missing.csv"))
    assert len(errors) == 1 and "cannot read file" in errors[0].message


def test_parameters_v_flag_requires_page_and_quote(tmp_path: Path) -> None:
    path = _write(tmp_path / "a.csv", PARAM_HEADER + "syn_v,process,V,2,1,3,-,syn,V,\n")
    _, warns = _levels(validate_parameters(path))
    assert len(warns) == 1 and "flag V but no page" in warns[0].message
    header = PARAM_HEADER.strip() + ",page,quote,verified_by,verified_on\n"
    row = 'syn_v,process,V,2,1,3,-,syn,V,,p. 12,"synthetic quote",tester,2026-10-06\n'
    assert validate_parameters(_write(tmp_path / "b.csv", header + row)) == []
    # a quote must say who read it; a verification date must be ISO
    row = 'syn_v,process,V,2,1,3,-,syn,V,,p. 12,"synthetic quote",,06/10/2026\n'
    errors, warns = _levels(validate_parameters(_write(tmp_path / "c.csv", header + row)))
    assert len(errors) == 1 and "verified_on" in errors[0].message
    assert len(warns) == 1 and "without page or verified_by" in warns[0].message


def test_load_parameters_reads_page_and_quote(tmp_path: Path) -> None:
    header = PARAM_HEADER.strip() + ",page,quote\n"
    path = _write(tmp_path / "p.csv", header + 'syn_v,process,V,2,1,3,-,syn,V,,"6, Table 6","q"\n')
    p = load_parameters(path)["syn_v"]
    assert (p.page, p.quote) == ("6, Table 6", "q")
    plain = _write(tmp_path / "plain.csv", PARAM_HEADER + PARAM_ROWS_OK)
    assert all(q.page == "" and q.quote == "" for q in load_parameters(plain).values())


# ---------------------------------------------------------------------------------------------
# sources.yaml
# ---------------------------------------------------------------------------------------------


def test_sources_clean_file_has_no_issues(tmp_path: Path) -> None:
    assert validate_sources(_write(tmp_path / "sources.yaml", SOURCES_OK)) == []


def test_sources_required_keys_status_confidence(tmp_path: Path) -> None:
    text = """\
schema_version: 0.1
updated: 2026-10-04
sources:
  - id: syn_missing
    name: Missing publisher and url
    module: supply
    status: get
    confidence: S
    access: open
    license: synthetic
  - id: syn_bad_values
    name: Bad status and flag
    publisher: Synthetic
    url: https://example.org/x
    module: supply
    status: maybe
    confidence: "V (read)"
    access: open
    license: synthetic
  - id: syn_comment_flag
    name: Flag with an inline comment inside a quoted string
    publisher: Synthetic
    url: https://example.org/y
    module: supply
    status: have
    confidence: "V # read in full"
    access: open
    license: synthetic
    accessed: 2026-01-01
    sha256: synthetic
    local_path: data/raw/synthetic.csv
"""
    errors, warns = _levels(validate_sources(_write(tmp_path / "s.yaml", text)))
    assert [(e.row, e.id, e.message) for e in errors] == [
        (4, "syn_missing", "missing required key(s): publisher, url"),
        (11, "syn_bad_values", "status 'maybe' is not one of have|get|lai|paid|build"),
        (11, "syn_bad_values", "confidence 'V (read)' is not one of V/S/K/D"),
    ]
    assert warns == []


def test_sources_url_rules(tmp_path: Path) -> None:
    base = (
        "schema_version: 0.1\nupdated: 2026-10-04\nsources:\n"
        "  - id: syn_url\n    name: n\n    publisher: p\n    module: m\n    status: get\n"
        "    confidence: S\n    access: open\n    license: l\n"
    )
    placeholder = _write(tmp_path / "a.yaml", base + "    url: TBD\n")
    errors, warns = _levels(validate_sources(placeholder))
    assert errors == [] and "placeholder" in warns[0].message
    garbage = _write(tmp_path / "b.yaml", base + "    url: ftp://example.org/file\n")
    errors, _ = _levels(validate_sources(garbage))
    assert "neither http(s)://" in errors[0].message
    also = _write(
        tmp_path / "c.yaml", base + "    url: https://example.org\n    also: [not-a-url]\n"
    )
    errors, warns = _levels(validate_sources(also))
    assert errors == [] and "'also' item(s)" in warns[0].message


def test_sources_duplicates_and_optional_keys(tmp_path: Path) -> None:
    text = """\
sources:
  - id: syn_dup
    name: First
    publisher: p
    url: https://example.org/1
    module: m
    status: have
    confidence: S
  - id: syn_dup
    name: Second
    name: Second again
    publisher: p
    url: https://example.org/2
    module: m
    status: get
    confidence: S
    access: open
    license: l
"""
    errors, warns = _levels(validate_sources(_write(tmp_path / "s.yaml", text)))
    assert sorted(e.message for e in errors) == [
        "duplicate id (first defined on line 2)",
        "duplicate key(s) name (YAML keeps only the last value)",
    ]
    messages = [w.message for w in warns]
    assert "top-level key 'schema_version' is missing" in messages
    assert "missing optional key(s): access, license" in messages
    assert any(m.startswith("status 'have' but download record incomplete") for m in messages)


def test_sources_unparseable_or_wrong_shape(tmp_path: Path) -> None:
    errors, _ = _levels(validate_sources(_write(tmp_path / "a.yaml", "sources: [unclosed\n")))
    assert len(errors) == 1 and errors[0].message.startswith("YAML parse error")
    errors, _ = _levels(validate_sources(_write(tmp_path / "b.yaml", "sources: {id: x}\n")))
    assert errors[0].message == "top level must be a mapping with a 'sources:' list"


# ---------------------------------------------------------------------------------------------
# projects_capex.csv
# ---------------------------------------------------------------------------------------------


def test_projects_clean_file_has_no_issues(tmp_path: Path) -> None:
    path = _write(tmp_path / "projects_capex.csv", PROJECTS_HEADER + PROJECT_ROW_OK)
    assert validate_projects_capex(path) == []


def test_projects_rules(tmp_path: Path) -> None:
    # SYNTHETIC rows; line numbers start at 2 (line 1 is the header).
    rows = (
        "1,A,x,SP,vinasse,1000,Nm3/d,nominal,10,5,2026,s,syn,S,\n"  # 2 ok
        "1,B,x,SP,vinasse,1000,Nm3/d,nominal,10,5,2026,s,syn,S,\n"  # 3 duplicate id
        "3,C,x,SP,vinasse,0,Nm3/d,nominal,10,5,2026,s,syn,S,\n"  # 4 capacity 0
        "4,D,x,SP,vinasse,abc,Nm3/d,nominal,10,5,2026,s,syn,S,\n"  # 5 non-numeric
        "5,E,x,SP,vinasse,500,t/yr,nominal,10,5,2026,s,syn,S,\n"  # 6 not gas flow
        "6,F,x,SP,vinasse,500,m3/d,nominal,10,5,2026,s,syn,S,\n"  # 7 no N basis
        "7,G,x,SP,vinasse,500,Nm3/d,nominal,ten,5,2026,s,syn,S/D,\n"  # 8 money + flag
        "8,H,x,SP,vinasse,500,Nm3/d,nominal,10,20,2026,s,syn,S,\n"  # 9 bndes 20 > total 10
        "9,I,x,SP,vinasse,,,pilot,15,,,pilot,syn,S,\n"  # 10 blank capacity ok
        "10,J,x,SP,vinasse,500,,nominal,,,2026,s,syn,S,\n"  # 11 value without unit
    )
    issues = validate_projects_capex(_write(tmp_path / "p.csv", PROJECTS_HEADER + rows))
    errors, warns = _levels(issues)
    assert [(e.row, e.message) for e in errors] == [
        (3, "duplicate id (first defined on line 2)"),
        (4, "capacity_value '0' must be > 0"),
        (5, "capacity_value 'abc' is not numeric"),
        (
            8,
            "confidence 'S/D' is not one of V/S/K/D (use a single flag; explain mixed "
            "provenance in notes)",
        ),
        (8, "investment_total_R$M 'ten' is not numeric"),
        (11, "capacity_value given without capacity_unit"),
    ]
    assert [w.row for w in warns] == [6, 7, 9]
    assert "'t/yr' is not a gas-flow unit" in warns[0].message
    assert "'m3/d' has no reference conditions" in warns[1].message
    assert warns[2].message == "bndes_R$M (20) exceeds investment_total_R$M (10)"


# ---------------------------------------------------------------------------------------------
# validate_all, summary, CLI
# ---------------------------------------------------------------------------------------------


def test_validate_all_and_issue_str(clean_registry: Path) -> None:
    assert validate_all(clean_registry) == []
    _write(clean_registry / "parameters.csv", PARAM_HEADER + "syn_x,process,X,2,1,3,,syn,S,\n")
    (issue,) = validate_all(clean_registry)
    assert str(issue) == (
        "ERROR parameters.csv:2 [syn_x]: unit is empty (use '-' for dimensionless values)"
    )


def test_summary_markdown_counts(clean_registry: Path) -> None:
    text = summary_markdown(clean_registry)
    # Parameters: syn_a = process/S, syn_b = supply/D -> totals V=0 S=1 K=0 D=1, 2 rows.
    assert "## Parameters (2)" in text
    assert "| process | 0 | 1 | 0 | 0 | 1 |" in text
    assert "| supply | 0 | 0 | 0 | 1 | 1 |" in text
    assert "| **total** | 0 | 1 | 0 | 1 | 2 |" in text
    # Sources: one 'supply' source with status get (have, get, lai, paid, build columns).
    assert "| supply | 0 | 1 | 0 | 0 | 0 | 1 |" in text
    assert "| S | 1 |" in text
    # Projects: one vinasse project flagged S.
    assert "| vinasse | 0 | 1 | 0 | 0 | 1 |" in text
    assert "0 error(s), 0 warning(s)" in text


def test_cli_validate_exit_codes(clean_registry: Path, capsys: pytest.CaptureFixture) -> None:
    assert main(["validate", "--registry-dir", str(clean_registry)]) == 0
    assert "0 error(s), 0 warning(s)" in capsys.readouterr().out
    # one warning (blank central) -> exit 0, but 1 with --strict
    _write(clean_registry / "parameters.csv", PARAM_HEADER + "syn_w,process,W,,1,3,-,syn,S,\n")
    assert main(["validate", "--registry-dir", str(clean_registry)]) == 0
    assert "WARNING parameters.csv:2 [syn_w]" in capsys.readouterr().out
    assert main(["validate", "--strict", "--registry-dir", str(clean_registry)]) == 1
    # one error -> exit 1
    _write(clean_registry / "parameters.csv", PARAM_HEADER + "syn_e,process,E,2,3,4,-,syn,S,\n")
    assert main(["validate", "--registry-dir", str(clean_registry)]) == 1
    capsys.readouterr()
    assert main(["summary", "--registry-dir", str(clean_registry)]) == 0
    assert capsys.readouterr().out.startswith("# Registry summary")
    assert main(["hash", "--registry-dir", str(clean_registry)]) == 0
    expected = param_hash(path=clean_registry / "parameters.csv")
    assert capsys.readouterr().out.strip() == expected


def test_python_dash_m_entry_point(clean_registry: Path) -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "engine.registry",
            "validate",
            "--registry-dir",
            str(clean_registry),
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "0 error(s), 0 warning(s)" in result.stdout


# ---------------------------------------------------------------------------------------------
# param_hash
# ---------------------------------------------------------------------------------------------


def test_param_hash_of_file_normalises_line_endings(tmp_path: Path) -> None:
    content = (PARAM_HEADER + PARAM_ROWS_OK).encode("utf-8")
    lf = _write(tmp_path / "lf.csv", content)
    crlf = _write(tmp_path / "crlf.csv", content.replace(b"\n", b"\r\n"))
    expected = hashlib.sha256(content).hexdigest()[:12]
    assert param_hash(path=lf) == expected
    assert param_hash(path=crlf) == expected
    assert param_hash(path=lf, length=64) == hashlib.sha256(content).hexdigest()


def test_param_hash_of_dict_is_canonical() -> None:
    # Canonical JSON written by hand: keys sorted, compact separators.
    expected = hashlib.sha256(b'{"a":1,"b":{"x":0.5,"y":[1,2]}}').hexdigest()[:12]
    assert param_hash({"b": {"y": [1, 2], "x": 0.5}, "a": 1}) == expected
    assert param_hash({"a": 1, "b": {"x": 0.5, "y": (1, 2)}}) == expected
    # numpy scalars hash like the equivalent Python float/int
    assert param_hash({"v": np.float64(0.3)}) == param_hash({"v": 0.3})
    assert param_hash({"v": np.int64(3)}) == param_hash({"v": 3})
    # different value or int-vs-float -> different hash
    assert param_hash({"v": 0.3}) != param_hash({"v": 0.31})
    assert param_hash({"v": 1}) != param_hash({"v": 1.0})


def test_param_hash_accepts_param_objects_and_rejects_bad_input() -> None:
    syn = Param("syn", "process", "Synthetic", 1.0, None, None, "-", "syn", "S", "", "1", "", "")
    assert len(param_hash({"syn": syn})) == 12
    with pytest.raises(TypeError):
        param_hash({1: 2})  # type: ignore[dict-item]
    with pytest.raises(TypeError):
        param_hash({"x": object()})
    with pytest.raises(ValueError):
        param_hash({"x": 1}, length=4)


# ---------------------------------------------------------------------------------------------
# Real registry (registry/ in git)
# ---------------------------------------------------------------------------------------------


def test_real_registry_loaders_unchanged() -> None:
    """The stable API still works and agrees with the validator's view of the file."""
    params = reg.load_parameters()
    assert params and all(isinstance(p, Param) for p in params.values())
    assert reg.get_param(next(iter(params))).id == next(iter(params))
    assert isinstance(reg.load_sources(), list)
    assert len(reg.load_projects_capex()) > 0


@pytest.mark.parametrize(
    "validator", [validate_parameters, validate_sources, validate_projects_capex]
)
def test_real_registry_has_no_validation_errors(validator) -> None:
    """Honest gate on the real registry.

    parameters.csv is expected to pass (it only has warnings: non-numeric TS/VS ranges, a blank
    central for ``capacity_factor``, a V flag without page/quote). sources.yaml and
    projects_capex.csv had real errors when this validator was written (2026-10-04: 72 sources
    missing required keys — mostly ``publisher`` — and project 12 flagged ``S/D``). Those are
    data gaps the registry owner must fill from the sources (never invented here), so the test
    xfails with the full list instead of hiding it; it turns into a pass once fixed.
    """
    errors = [i for i in validator() if i.level == "error"]
    if errors:
        pytest.xfail(f"{len(errors)} registry error(s):\n" + "\n".join(map(str, errors)))
    assert errors == []


# ---------------------------------------------------------------------------------------------
# references.csv (docs/08 §8) — SYNTHETIC rows, made-up DOIs on example domains
# ---------------------------------------------------------------------------------------------

REF_HEADER = (
    "ref_id,kind,authors,year,title,container,volume,issue,pages,doi,url,used_for,ref_check,"
    "checked_on,check_evidence,value_check,notes\n"
)
REF_ROW_OK = (
    "syn_ref,article,Doe J,2020,Synthetic title,Synthetic Journal,1,2,3-4,10.9999/syn.1,,"
    "parameters.csv:syn_a; docs/23,two_sources,2026-10-06,"
    "https://example.org/a; https://example.net/b,syn_a=seen_in_abstract,\n"
)


def _refs(tmp_path: Path, rows: str, params: str = PARAM_ROWS_OK) -> list[Issue]:
    _write(tmp_path / "parameters.csv", PARAM_HEADER + params)
    return reg.validate_references(_write(tmp_path / "references.csv", REF_HEADER + rows))


def test_references_clean_file_has_no_issues(tmp_path: Path) -> None:
    assert _refs(tmp_path, REF_ROW_OK) == []


@pytest.mark.parametrize(
    "old, new, message",
    [
        ("syn_ref,article", "syn_ref,blog", "kind"),
        ("10.9999/syn.1", "https://doi.org/10.9999/syn.1", "doi"),
        (",2020,", ",20,", "year"),
        ("parameters.csv:syn_a; docs/23", "", "used_for is empty"),
        ("parameters.csv:syn_a; docs/23", "parameters.csv:syn_zz", "unknown parameter"),
        ("https://example.org/a; https://example.net/b", "https://example.org/a", "two different"),
        ("2026-10-06", "", "checked_on"),
        ("syn_a=seen_in_abstract", "syn_a=looks_right", "value_check"),
        ("two_sources", "verified", "ref_check"),
    ],
)
def test_references_errors(tmp_path: Path, old: str, new: str, message: str) -> None:
    errors, _ = _levels(_refs(tmp_path, REF_ROW_OK.replace(old, new)))
    assert any(message in e.message for e in errors), errors


def test_references_duplicate_ids(tmp_path: Path) -> None:
    errors, _ = _levels(_refs(tmp_path, REF_ROW_OK + REF_ROW_OK))
    assert any("duplicate ref_id" in e.message for e in errors)


def test_references_warnings(tmp_path: Path) -> None:
    # not double-checked -> warning; pending needs no date or evidence
    row = REF_ROW_OK.replace("two_sources,2026-10-06", "pending,")
    errors, warns = _levels(_refs(tmp_path, row))
    assert errors == []
    assert any("not double-checked" in w.message for w in warns)
    # a parameter citing a paper with no reference row
    params = PARAM_ROWS_OK + "syn_c,process,C,1,,,-,Roe et al. 2019,S,\n"
    _, warns = _levels(_refs(tmp_path, REF_ROW_OK, params))
    assert any("syn_c" in w.message and "no references.csv row" in w.message for w in warns)
    # a V parameter whose only reference is not double-checked
    params_v = PARAM_ROWS_OK.replace("Synthetic fixture,S,", "Synthetic fixture,V,", 1)
    _, warns = _levels(_refs(tmp_path, row, params_v))
    assert any("flagged V" in w.message for w in warns)


def test_validate_all_reads_references_when_present(clean_registry: Path) -> None:
    assert validate_all(clean_registry) == []
    _write(clean_registry / "references.csv", REF_HEADER + REF_ROW_OK.replace("syn_ref", "Bad"))
    (issue,) = validate_all(clean_registry)
    assert "snake_case" in issue.message
    _write(clean_registry / "references.csv", REF_HEADER + REF_ROW_OK)
    text = summary_markdown(clean_registry)
    assert "## References (1)" in text and "| two_sources | 1 |" in text


# ---------------------------------------------------------------------------------------------
# value_evidence.csv (docs/08 §6, ADR-0015) — SYNTHETIC rows
# ---------------------------------------------------------------------------------------------

EV_HEADER = (
    "evidence_id,param_id,ref_id,pdf_page,printed_page,location,quote,value,unit,conditions,"
    "origin,support,check,cited_ref,notes\n"
)
EV_ROW_OK = (
    "syn_ref:syn_a:0,syn_a,syn_ref,3,103,Table 1,Synthetic verbatim quote,2,kg per t,"
    "synthetic,own_measurement,supports_central,human_audited,,\n"
)


def _evidence(tmp_path: Path, rows: str) -> list[Issue]:
    _write(tmp_path / "parameters.csv", PARAM_HEADER + PARAM_ROWS_OK)
    _write(tmp_path / "references.csv", REF_HEADER + REF_ROW_OK)
    return reg.validate_value_evidence(_write(tmp_path / "value_evidence.csv", EV_HEADER + rows))


def test_value_evidence_clean_file_has_no_issues(tmp_path: Path) -> None:
    assert _evidence(tmp_path, EV_ROW_OK) == []


@pytest.mark.parametrize(
    "old, new, message",
    [
        (",syn_a,syn_ref,", ",syn_zz,syn_ref,", "not in parameters.csv"),
        (",syn_a,syn_ref,", ",syn_a,other_ref,", "not in references.csv"),
        (",3,103,", ",0,103,", "pdf_page"),
        (",3,103,", ",p3,103,", "pdf_page"),
        ("Synthetic verbatim quote", "", "quote is empty"),
        ("own_measurement", "measured", "origin"),
        ("supports_central", "agrees", "support"),
        ("human_audited", "looks_right", "check"),
        ("syn_ref:syn_a:0,", ",", "empty evidence_id"),
    ],
)
def test_value_evidence_errors(tmp_path: Path, old: str, new: str, message: str) -> None:
    errors, _ = _levels(_evidence(tmp_path, EV_ROW_OK.replace(old, new)))
    assert any(message in e.message for e in errors), errors


def test_value_evidence_duplicates_and_audit_warning(tmp_path: Path) -> None:
    errors, _ = _levels(_evidence(tmp_path, EV_ROW_OK + EV_ROW_OK))
    assert any("duplicate evidence_id" in e.message for e in errors)
    llm = EV_ROW_OK.replace("human_audited", "llm_double_read")
    llm2 = llm.replace("syn_a:0", "syn_a:1").replace("llm_double_read", "llm_corrected")
    errors, warns = _levels(_evidence(tmp_path, llm + llm2))
    assert errors == []
    (warn,) = warns
    assert "2 row(s) not human_audited" in warn.message


def test_validate_all_reads_value_evidence_when_present(clean_registry: Path) -> None:
    _write(clean_registry / "references.csv", REF_HEADER + REF_ROW_OK)
    _write(clean_registry / "value_evidence.csv", EV_HEADER + EV_ROW_OK)
    assert validate_all(clean_registry) == []
    text = summary_markdown(clean_registry)
    assert "## Value evidence (1)" in text and "| supports_central | 0 | 0 | 0 | 1 | 1 |" in text
    _write(clean_registry / "value_evidence.csv", EV_HEADER + EV_ROW_OK.replace(",3,", ",x,"))
    (issue,) = validate_all(clean_registry)
    assert issue.file == "value_evidence.csv" and "pdf_page" in issue.message


@pytest.mark.parametrize(
    "path, validator",
    [
        (reg.REFERENCES_CSV, reg.validate_references),
        (reg.VALUE_EVIDENCE_CSV, reg.validate_value_evidence),
    ],
)
def test_real_references_and_evidence_have_no_errors(path: Path, validator) -> None:
    """The committed references.csv and value_evidence.csv pass with no errors (warnings for
    references not double-checked and rows not human-audited are expected)."""
    if not path.exists():
        pytest.skip(f"{path.name} not present")
    errors = [i for i in validator() if i.level == "error"]
    assert errors == [], "\n".join(map(str, errors))
