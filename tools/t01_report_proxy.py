"""Generate transparent baseline-vs-PoC *metadata proxy* report without hidden GT.

Usage: python -m tools.t01_report_proxy
Not a substitute for the instructor's official src.evaluate.
"""
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from src.pipeline import DIMS, coverage_table


def _score(picks, cand, targets):
    cov = coverage_table(picks, cand, targets)
    total = float(cov["weight"].sum())
    covered = cov[cov["estimated_covered"] == 1]
    hard = cov[cov["is_hard"] == 1]
    ids = picks["clip_id"].astype(str)
    by_id = cand.set_index("clip_id")
    combos = [tuple(by_id.loc[c, d] for d in DIMS) for c in ids]
    return {
        "w": round(float(covered["weight"].sum()) / total, 4),
        "covered": int(len(covered)),
        "hard": f"{int(hard['estimated_covered'].sum())}/{len(hard)}",
        "duplicates": len(combos) - len(set(combos)),
        "cost": float(by_id.loc[list(ids), "cost_min"].sum()),
    }


def main():
    fixture = Path("fixtures/t01_coverage")
    cand = pd.read_csv(fixture / "candidates.csv")
    targets = pd.read_csv(fixture / "targets.csv")
    baseline = pd.read_csv("out/baseline/pick.csv").sort_values("rank")
    poc = pd.read_csv("out/poc/pick.csv").sort_values("rank")
    rows = []
    for k in (10, 20, 30):
        for label, picks in (("Random baseline", baseline), ("Greedy PoC", poc)):
            if len(picks) < k:
                raise ValueError(f"{label} has fewer than {k} picks")
            rows.append({"K": k, "Method": label, **_score(picks.head(k), cand, targets)})
    df = pd.DataFrame(rows)
    Path("reports").mkdir(exist_ok=True)
    table = ["# T01 – Metadata-proxy comparison only (NOT official verified-tag evaluation)", "",
             "This table uses visible planner metadata, which the fixture warns can be wrong/unknown.",
             "Do not report these numbers as official Weighted Coverage@K from verified GT.", "",
             "| K | Method | Proxy weighted coverage | Cells covered | Hard cells covered | Duplicate scenarios | Cost (minutes) |",
             "|---:|---|---:|---:|---|---:|---:|"]
    for r in rows:
        table.append(f"| {r['K']} | {r['Method']} | {r['w']:.4f} | {r['covered']}/15 | {r['hard']} | {r['duplicates']} | {r['cost']:.1f} |")
    Path("reports/table1_proxy_only.md").write_text("\n".join(table) + "\n", encoding="utf-8")
    xs = [10, 20, 30]
    a = [r["w"] for r in rows if r["Method"] == "Random baseline"]
    b = [r["w"] for r in rows if r["Method"] == "Greedy PoC"]
    width = 0.36
    plt.figure(figsize=(7.8, 4.5))
    plt.bar([x - width/2 for x in range(3)], a, width, label="Random baseline")
    plt.bar([x + width/2 for x in range(3)], b, width, label="Greedy PoC")
    plt.xticks([0, 1, 2], [f"K={x}" for x in xs])
    plt.ylabel("Weighted coverage (visible metadata proxy)")
    plt.ylim(0, 1)
    plt.title("T01: coverage comparison (NOT official GT evaluation)")
    plt.legend()
    plt.tight_layout()
    plt.savefig("reports/g07_t01_proxy_coverage.png", dpi=160)
    plt.close()
    print(df.to_string(index=False))
    print("Wrote reports/table1_proxy_only.md and reports/g07_t01_proxy_coverage.png")


if __name__ == "__main__":
    main()
