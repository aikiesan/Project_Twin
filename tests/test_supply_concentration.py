"""engine.supply.concentration."""

import pandas as pd
import pytest

from engine.supply.concentration import count_for_share, cumulative_share


def test_cumulative_share_sorted():
    c = cumulative_share(pd.Series({"a": 1.0, "b": 6.0, "c": 3.0}))
    assert list(c.index) == ["b", "c", "a"]
    assert c["cum_share"].tolist() == pytest.approx([0.6, 0.9, 1.0])
    assert c["rank"].tolist() == [1, 2, 3]


def test_count_for_share():
    v = pd.Series([50.0, 30.0, 10.0, 10.0, None])
    assert count_for_share(v, [0.5, 0.8, 0.85, 1.0]) == {0.5: 1, 0.8: 2, 0.85: 3, 1.0: 4}


def test_zero_total():
    with pytest.raises(ValueError):
        cumulative_share(pd.Series([0.0, None]))
