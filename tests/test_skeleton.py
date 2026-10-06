"""Walking-skeleton runner (ADR-0010): config checks, ANP comparison, run outputs, CLI.

Uses the ANP evidence CSV held in git and a fixture config whose cane values are test inputs.
"""

import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from engine.skeleton import (
    ANP_MONTHLY_CSV,
    SKELETON_MILLS_YAML,
    MissingInputError,
    compare_with_anp,
    load_anp_monthly,
    load_mill_configs,
    main,
    missing_inputs,
    nameplate_from_anp,
    run_skeleton,
)

FIXTURE = Path(__file__).parent / "fixtures" / "skeleton_mills_test.yaml"


def test_registry_config_is_valid():
    mills, x_ch4 = load_mill_configs(SKELETON_MILLS_YAML)
    assert {"costa_pinto", "narandiba"} <= set(mills)
    assert 0 < x_ch4 <= 1
    anp_ids = set(pd.read_csv(ANP_MONTHLY_CSV)["plant_id"])
    for m in mills.values():
        assert m.anp_plant_id in anp_ids


def _write(tmp_path, doc):
    path = tmp_path / "mills.yaml"
    path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return path


def _doc(**mill_overrides):
    mill = {
        "name": "x",
        "anp_plant_id": "sp_cocal_narandiba",
        "strategy": "S0",
        "cane_t": {2025: {"value": 1.0, "source": "s", "confidence": "K"}},
        "ad_shares": {"vinasse": 1.0, "filter_cake": 1.0, "straw": 0.0},
    }
    mill.update(mill_overrides)
    return {"x_ch4": 0.6, "mills": {"m": mill}}


@pytest.mark.parametrize(
    "override, message",
    [
        ({"cane_t": {2025: {"value": 1.0, "source": "TODO", "confidence": "K"}}}, "source"),
        ({"cane_t": {2025: {"value": 1.0, "source": "s", "confidence": "X"}}}, "confidence"),
        ({"cane_t": {2025: {"value": -1.0, "source": "s", "confidence": "K"}}}, ">= 0"),
        ({"ad_shares": {"vinasse": 1.0, "filter_cake": 1.0}}, "ad_shares"),
        ({"ad_shares": {"vinasse": 1.5, "filter_cake": 1.0, "straw": 0.0}}, "fractions"),
        ({"anp_plant_id": ""}, "anp_plant_id"),
    ],
)
def test_config_errors(tmp_path, override, message):
    with pytest.raises(ValueError, match=message):
        load_mill_configs(_write(tmp_path, _doc(**override)))


def test_missing_inputs_and_refusal():
    mills, _ = load_mill_configs(FIXTURE)
    assert missing_inputs(mills["narandiba_test"], 2025) == []
    assert missing_inputs(mills["narandiba_test"], 2026) == ["cane_t[2026]"]
    assert missing_inputs(mills["narandiba_test"], 2030) == ["cane_t[2030]"]
    assert missing_inputs(mills["storage_test"], 2025) == []
    assert missing_inputs(mills["narandiba_test"], 2025, "S1") == ["storage block (strategy S1)"]
    empty = missing_inputs(mills["storage_empty_test"], 2025)[0]
    assert "store_frac" in empty and "loss_frac_per_month" in empty and "loss_source" in empty
    assert "strategy S3" in missing_inputs(mills["unknown_strategy_test"], 2025)[0]
    with pytest.raises(MissingInputError, match="cane_t"):
        run_skeleton("narandiba_test", 2026, config_path=FIXTURE, out_dir=None)
    with pytest.raises(MissingInputError, match="S3"):
        run_skeleton("unknown_strategy_test", 2025, config_path=FIXTURE, out_dir=None)
    with pytest.raises(MissingInputError, match="storage needs"):
        run_skeleton("storage_empty_test", 2025, config_path=FIXTURE, out_dir=None)
    with pytest.raises(KeyError):
        run_skeleton("nope", 2025, config_path=FIXTURE, out_dir=None)


def test_anp_loader_and_nameplate():
    anp = load_anp_monthly("sp_cocal_narandiba")
    assert anp["month"].is_monotonic_increasing
    assert anp["month"].str.fullmatch(r"\d{4}-\d{2}").all()
    bm, bg = nameplate_from_anp(anp, 2025)
    row = anp[anp["month"] == "2026-03"].iloc[0]
    assert (bm, bg) == (row["cap_biometano_m3d"], row["cap_biogas_m3d"])
    with pytest.raises(KeyError):
        load_anp_monthly("no_such_plant")


def test_comparison_math():
    months = ["2025-11", "2025-12", "2026-01"]
    sim = pd.DataFrame({"month": months, "days": [30, 31, 31], "biogas_nm3": [300.0, 0, 62.0]})
    anp = pd.DataFrame({"month": months[:2], "vol_biogas_m3d": [5.0, 0.0]})
    t, m = compare_with_anp(sim, anp, cap_biogas_m3_d=8.0)
    t = t.set_index("month")
    assert t.loc["2025-11", "sim_biogas_capped_nm3_d"] == 8.0  # 10/d capped at 8
    assert t.loc["2025-11", "sim_util_pct"] == pytest.approx(100)
    assert t.loc["2025-11", "obs_util_pct"] == pytest.approx(62.5)
    assert t.loc["2025-12", "obs_near_zero"] is True
    assert t.loc["2026-01", "obs_near_zero"] is None  # not in the ANP series
    assert m["n_months_observed"] == 2
    assert m["n_months_compared"] == 1
    assert m["n_obs_near_zero"] == 1
    assert m["mae_util_pp"] == pytest.approx(37.5)
    assert m["bias_util_pp"] == pytest.approx(37.5)
    assert m["volume_ratio_sim_obs"] == pytest.approx(8 / 5)
    assert m["offseason_share_sim"] == 0 and m["offseason_share_obs"] == 0


def test_run_writes_outputs_and_is_reproducible(tmp_path):
    run = run_skeleton("narandiba_test", 2025, config_path=FIXTURE, out_dir=tmp_path)
    assert run.run_id.startswith("skel-narandiba_test-2025-")
    assert run.out_path == tmp_path / run.run_id
    for name in ("monthly.csv", "comparison.csv", "summary.json"):
        assert (run.out_path / name).is_file()
    summary = json.loads((run.out_path / "summary.json").read_text(encoding="utf-8"))
    assert summary["inputs"]["cane_t"] == {
        "value": 1e6,
        "source": "test fixture",
        "confidence": "K",
    }
    assert summary["inputs"]["x_ch4"] == 0.6
    assert summary["caveats"]
    assert set(summary["registry_params"].values()) <= {"V", "S", "K", "D"}
    assert sum(summary["flag_counts"].values()) == len(summary["registry_params"])
    assert summary["results"]["lcob"]["lcob_brl_per_nm3"] > 0
    assert len(run.monthly) == 12

    again = run_skeleton("narandiba_test", 2025, config_path=FIXTURE, out_dir=None)
    assert again.run_id == run.run_id
    other = run_skeleton("narandiba_test", 2025, config_path=FIXTURE, x_ch4=0.65, out_dir=None)
    assert other.run_id != run.run_id


def test_s0_has_no_off_season_output_but_narandiba_does():
    """The diagnostic the skeleton exists for: S0 cannot explain Narandiba's off-season output."""
    run = run_skeleton("narandiba_test", 2025, config_path=FIXTURE, out_dir=None)
    c = run.summary["comparison_with_anp"]
    assert c["offseason_share_sim"] == 0
    assert c["offseason_share_obs"] > 0.2  # ANP Dec 2025 - Mar 2026: 30-39 % utilization


def test_us_anchor_needs_an_exchange_rate():
    run = run_skeleton("narandiba_test", 2025, config_path=FIXTURE, out_dir=None)
    fiesp = [a for a in run.summary["results"]["anchors"] if a["anchor_id"] == "lcob_fiesp"][0]
    assert fiesp["engine_value"] is None and fiesp["within_range"] is None
    run = run_skeleton("narandiba_test", 2025, config_path=FIXTURE, brl_per_usd=5.0, out_dir=None)
    fiesp = [a for a in run.summary["results"]["anchors"] if a["anchor_id"] == "lcob_fiesp"][0]
    assert fiesp["engine_value"] > 0


def test_cli(tmp_path, capsys):
    assert main(["--config", str(FIXTURE), "list"]) == 0
    out = capsys.readouterr().out
    assert "narandiba_test" in out and "missing cane_t[2026]" in out
    code = main(
        ["--config", str(FIXTURE), "run", "--mill", "narandiba_test", "--crop-year", "2026"]
    )
    assert code == 2
    assert "Cannot run" in capsys.readouterr().out
    args = ["run", "--mill", "narandiba_test", "--crop-year", "2025", "--out", str(tmp_path)]
    assert main(["--config", str(FIXTURE), *args]) == 0
    assert "run_id skel-narandiba_test-2025-" in capsys.readouterr().out


def test_s1_moves_output_into_the_off_season():
    s0 = run_skeleton("storage_test", 2025, config_path=FIXTURE, strategy="S0", out_dir=None)
    s1 = run_skeleton("storage_test", 2025, config_path=FIXTURE, out_dir=None)
    assert s1.summary["inputs"]["strategy"] == "S1"
    assert s0.run_id != s1.run_id
    assert s0.summary["comparison_with_anp"]["offseason_share_sim"] == 0
    assert s1.summary["comparison_with_anp"]["offseason_share_sim"] > 0
    bal = s1.summary["results"]["storage_balance"]
    stored = bal["filter_cake_stored_t_fm"]
    assert stored > 0
    assert stored == pytest.approx(
        bal["filter_cake_released_t_fm"]
        + bal["filter_cake_storage_loss_t_fm"]
        + bal["filter_cake_end_stock_t_fm"]
    )
    assert s1.summary["inputs"]["storage"]["loss_source"] == "test fixture"
    # off-season feed is cake only, so the TS check flags those months (documented v0 limit)
    assert set(s1.summary["results"]["months_infeasible"]) >= {"2025-12", "2026-03"}
