"""engine.ingest.municipalities: IBGE code -> name from the tables the project holds."""

import pandas as pd
import pytest

from engine.ingest.municipalities import name_map, read_names


def test_panel_csv_with_municipality_name_and_text_codes(tmp_path):
    p = tmp_path / "panel.csv"
    pd.DataFrame(
        {
            "ibge_code": ["3554508", "3539509", "5300108"],
            "municipality_name": ["Tietê", "Pitangueiras", "Brasília"],
            "other": [1, 2, 3],
        }
    ).to_csv(p, index=False)
    t = read_names(p)
    assert list(t["ibge_code"]) == [3554508, 3539509]  # SP only, int
    assert name_map(p)[3554508] == "Tietê"


def test_missing_name_column_is_explicit(tmp_path):
    p = tmp_path / "bad.csv"
    pd.DataFrame({"ibge_code": ["3554508"], "label": ["x"]}).to_csv(p, index=False)
    with pytest.raises(KeyError, match="name column"):
        read_names(p)


def test_read_names_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_names(tmp_path)
