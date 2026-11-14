"""Holdout selection using the fixed algorithm; NEVER reads hidden verified tags.

Run: python -m tools.t01_holdout
"""
from pathlib import Path

import pandas as pd

from src.pipeline import coverage_table, greedy_pick


def main():
    root = Path("fixtures/t01_coverage")
    candidates = pd.read_csv(root / "holdout_candidates.csv")
    targets = pd.read_csv(root / "targets.csv")
    out = Path("out")
    out.mkdir(exist_ok=True)
    picks = greedy_pick(candidates, targets, 6)
    picks[["clip_id", "rank"]].to_csv(out / "pick_holdout.csv", index=False)
    cov = coverage_table(picks, candidates, targets)
    cov.to_csv(out / "coverage_holdout_proxy.csv", index=False)
    print("Holdout: 6 clip IDs, metadata estimated coverage:",
          int(cov["estimated_covered"].sum()), "/", len(cov), "(NOT verified GT)")
    print("Wrote out/pick_holdout.csv and out/coverage_holdout_proxy.csv")


if __name__ == "__main__":
    main()
