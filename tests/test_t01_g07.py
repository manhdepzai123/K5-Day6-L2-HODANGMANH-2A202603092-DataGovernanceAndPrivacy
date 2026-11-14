"""G07-owned T01 normal and failure/edge tests; no GT files used."""
from pathlib import Path

import pandas as pd
import pytest

from src.pipeline import coverage_table, greedy_pick

FIXTURE = Path(__file__).resolve().parents[1] / "fixtures" / "t01_coverage"


def test_t01_selects_30_unique_and_deterministic():
    c = pd.read_csv(FIXTURE / "candidates.csv")
    t = pd.read_csv(FIXTURE / "targets.csv")
    a = greedy_pick(c, t, 30)
    b = greedy_pick(c, t, 30)
    assert len(a) == 30
    assert a["clip_id"].nunique() == 30
    assert a["clip_id"].tolist() == b["clip_id"].tolist()
    coverage = coverage_table(a, c, t)
    assert len(coverage) == 15
    assert 0 <= coverage["estimated_covered"].mean() <= 1


def test_t01_invalid_k_fails_loudly():
    c = pd.read_csv(FIXTURE / "candidates.csv")
    t = pd.read_csv(FIXTURE / "targets.csv")
    with pytest.raises(ValueError, match="K="):
        greedy_pick(c, t, 1000)


def test_t01_duplicate_clip_id_fails_loudly():
    c = pd.read_csv(FIXTURE / "candidates.csv")
    t = pd.read_csv(FIXTURE / "targets.csv")
    c.loc[1, "clip_id"] = c.loc[0, "clip_id"]
    with pytest.raises(ValueError, match="duplicate"):
        greedy_pick(c, t, 30)
