"""G07 T01 Coverage Planner PoC, offline and with auditable human review.

Run with: python -m src.main --config configs/lab.yaml --output out/poc --offline --seed 42
This source intentionally never opens fixtures/*/gt/.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .common.context import RunContext
from .common.decision import Decision, write_decision
from .common.manifest import verify_manifest
from .common.review import (
    apply_overrides,
    load_review_decisions,
    make_review_queue,
    write_review_queue,
)
from .metrics.tracks import get_track

DIMS = ["route", "weather", "light", "object"]
CANDIDATE_COLS = ["clip_id", *DIMS, "risk", "cost_min"]
TARGET_COLS = ["cell_id", *DIMS, "weight", "is_hard"]


def _require_columns(df: pd.DataFrame, cols: list[str], label: str) -> None:
    missing = sorted(set(cols) - set(df.columns))
    if missing:
        raise ValueError(f"{label}: missing columns {missing}")


def _normalise_candidates(candidates: pd.DataFrame) -> pd.DataFrame:
    _require_columns(candidates, CANDIDATE_COLS, "candidates.csv")
    out = candidates.copy()
    if out["clip_id"].isna().any() or out["clip_id"].astype(str).duplicated().any():
        raise ValueError("candidates.csv: empty/duplicate clip_id")
    out["clip_id"] = out["clip_id"].astype(str)
    for d in DIMS:
        out[d] = out[d].fillna("unknown").astype(str)
    out["risk"] = out["risk"].fillna("unknown").astype(str).str.lower()
    out["cost_min"] = pd.to_numeric(out["cost_min"], errors="coerce")
    if out["cost_min"].isna().any() or (out["cost_min"] < 0).any():
        raise ValueError("candidates.csv: invalid cost_min")
    return out.sort_values("clip_id", kind="mergesort").reset_index(drop=True)


def _normalise_targets(targets: pd.DataFrame) -> pd.DataFrame:
    _require_columns(targets, TARGET_COLS, "targets.csv")
    out = targets.copy()
    if out["cell_id"].isna().any() or out["cell_id"].astype(str).duplicated().any():
        raise ValueError("targets.csv: empty/duplicate cell_id")
    out["cell_id"] = out["cell_id"].astype(str)
    out["weight"] = pd.to_numeric(out["weight"], errors="coerce")
    out["is_hard"] = pd.to_numeric(out["is_hard"], errors="coerce")
    if out["weight"].isna().any() or (out["weight"] <= 0).any():
        raise ValueError("targets.csv: weights must be positive numbers")
    if out["is_hard"].isna().any() or not out["is_hard"].isin([0, 1]).all():
        raise ValueError("targets.csv: is_hard must be 0 or 1")
    return out


def _matched_cells(clip: pd.Series, targets: pd.DataFrame) -> set[str]:
    return {
        str(t["cell_id"])
        for _, t in targets.iterrows()
        if all(str(t[d]) == "*" or str(t[d]) == str(clip[d]) for d in DIMS)
    }


def greedy_pick(candidates: pd.DataFrame, targets: pd.DataFrame, k: int) -> pd.DataFrame:
    """Deterministic weighted-greedy selection on *visible metadata*, not verified GT."""
    candidates = _normalise_candidates(candidates)
    targets = _normalise_targets(targets)
    if not 1 <= k <= len(candidates):
        raise ValueError(f"K={k} must be between 1 and {len(candidates)}")
    weights = dict(zip(targets["cell_id"], targets["weight"].astype(float)))
    hits = {r["clip_id"]: _matched_cells(r, targets) for _, r in candidates.iterrows()}
    available = candidates.set_index("clip_id", drop=False)
    used_scenarios: set[tuple[str, ...]] = set()
    covered: set[str] = set()
    chosen = []

    for position in range(1, k + 1):
        best_id = None
        best_key = None
        for clip_id, clip in available.iterrows():
            gain = sum(weights[c] for c in hits[clip_id] - covered)
            scenario = tuple(str(clip[d]) for d in DIMS)
            novelty = int(scenario not in used_scenarios)
            key = (gain, novelty, -float(clip["cost_min"]))
            # Available is sorted by ID, so exact ties prefer lowest clip_id.
            if best_key is None or key > best_key:
                best_id, best_key = clip_id, key
        assert best_id is not None and best_key is not None
        clip = available.loc[best_id]
        unknown = any(str(clip[d]).lower() == "unknown" for d in DIMS)
        risk = str(clip["risk"]).lower()
        review_score = (20.0 if unknown else 0.0) + {"high": 10.0, "med": 5.0}.get(risk, 0.0) + best_key[0] / 100.0
        chosen.append({
            "clip_id": best_id,
            "rank": position,
            "score": review_score,
            "reason": f"new_weight={best_key[0]:g}; risk={risk}; unknown={unknown}",
            "suggested_action": "escalate" if unknown else "review",
        })
        covered.update(hits[best_id])
        used_scenarios.add(tuple(str(clip[d]) for d in DIMS))
        available = available.drop(index=best_id)
    return pd.DataFrame(chosen)


def coverage_table(picks: pd.DataFrame, candidates: pd.DataFrame, targets: pd.DataFrame) -> pd.DataFrame:
    """Metadata-based estimated coverage; NOT the hidden verified-tag metric."""
    candidates = _normalise_candidates(candidates).set_index("clip_id")
    targets = _normalise_targets(targets)
    chosen_ids = picks["clip_id"].astype(str).tolist()
    if len(chosen_ids) != len(set(chosen_ids)) or set(chosen_ids) - set(candidates.index):
        raise ValueError("pick.csv: duplicate or unknown clip_id")
    matched = {}
    for clip_id in chosen_ids:
        for cell_id in _matched_cells(candidates.loc[clip_id], targets):
            matched.setdefault(cell_id, []).append(clip_id)
    out = targets.copy()
    out["estimated_covered"] = out["cell_id"].map(lambda c: int(c in matched))
    out["evidence_clip_ids"] = out["cell_id"].map(lambda c: ";".join(matched.get(c, [])))
    return out


# --------------------------------------------------------------- 01 LOAD
def load(ctx: RunContext) -> dict:
    manifest = ctx.input_dir / "manifest.csv"
    problems = verify_manifest(manifest) if manifest.exists() else [{"problem": "no_manifest"}]
    if problems:
        ctx.audit.log(actor="pipeline", action="provenance_problems", item_id=str(manifest), after=problems[:20])
        if ctx.config.get("strict_provenance", True):
            raise ValueError(f"provenance check failed: {problems[:3]}")
    candidates = _normalise_candidates(pd.read_csv(ctx.input_dir / "candidates.csv"))
    targets = _normalise_targets(pd.read_csv(ctx.input_dir / "targets.csv"))
    return {"candidates": candidates, "targets": targets}


# --------------------------------------------------------------- 02 PROCESS
def process(ctx: RunContext, data: dict) -> pd.DataFrame:
    return greedy_pick(data["candidates"], data["targets"], int(ctx.param("k", 30)))


# --------------------------------------------------------------- 03 RANK
def rank(ctx: RunContext, scored: pd.DataFrame) -> pd.DataFrame:
    budget = int(ctx.param("budget", 20))
    if not 1 <= budget <= len(scored):
        raise ValueError("Review budget must be 1..K")
    queue = make_review_queue(
        scored, "clip_id", "score", budget,
        reason_col="reason", action_col="suggested_action",
    )
    write_review_queue(queue, ctx.out("review_queue.csv"))
    return queue


# --------------------------------------------------------------- 04 REVIEW
def review(ctx: RunContext, scored: pd.DataFrame, queue: pd.DataFrame, candidates: pd.DataFrame) -> pd.DataFrame:
    final = scored.copy()
    path = ctx.output_dir / "review_queue_reviewed.csv"
    ctx.stats["n_reviewed"] = 0
    ctx.stats["n_escalated"] = 0
    ctx.stats["n_pending_new_clips"] = 0
    if not path.exists():
        return final

    decisions = load_review_decisions(path)
    queue_ids = set(queue["item_id"].astype(str))
    if set(decisions["item_id"].astype(str)) - queue_ids:
        raise ValueError("Reviewed CSV contains clip IDs not in CURRENT review_queue.csv; refresh the reviewed file")
    if decisions["item_id"].duplicated().any():
        raise ValueError("Reviewed CSV has duplicated item_id decisions")
    pool = set(candidates["clip_id"].astype(str))
    proposed = final["clip_id"].astype(str).tolist()
    for r in decisions.itertuples(index=False):
        if r.reviewer_decision in ("edit", "reject"):
            replacement = str(r.override_value).strip()
            if not replacement or replacement not in pool:
                raise ValueError(f"{r.reviewer_decision} for {r.item_id} requires valid replacement clip_id in override_value")
            if replacement != r.item_id and replacement in proposed:
                raise ValueError(f"Replacement {replacement} already selected; choose an unselected clip")
            if replacement == r.item_id:
                raise ValueError("Replacement must differ from the rejected/edited clip")
            proposed[proposed.index(r.item_id)] = replacement
            ctx.stats["n_pending_new_clips"] += 1
    final = apply_overrides(final, decisions, "clip_id", "clip_id", audit=ctx.audit)
    for r in decisions.itertuples(index=False):
        ctx.audit.log(actor=r.reviewer, action=f"review:{r.reviewer_decision}", item_id=r.item_id,
                      after=r.override_value if r.override_value else r.reviewer_decision, reason=r.review_note)
    ctx.stats["n_reviewed"] = len(decisions)
    ctx.stats["n_escalated"] = int(decisions["reviewer_decision"].isin(["escalate", "skip"]).sum())
    return final


def _create_risk_review_queue(ctx: RunContext, coverage: pd.DataFrame) -> pd.DataFrame:
    hard = coverage[coverage["is_hard"] == 1].copy()
    hard["missing_first"] = 1 - hard["estimated_covered"]
    hard = hard.sort_values(["missing_first", "weight", "cell_id"], ascending=[False, False, True]).head(3)
    q = hard[["cell_id", "weight", "estimated_covered", "evidence_clip_ids"]].copy()
    for col in ["reviewer", "reviewer_decision", "review_note", "reviewed_at"]:
        q[col] = ""
    q.to_csv(ctx.out("risk_cells_review_queue.csv"), index=False)
    return q


def _risk_review_stats(ctx: RunContext, risk_queue: pd.DataFrame) -> tuple[int, int]:
    path = ctx.output_dir / "risk_cells_reviewed.csv"
    if not path.exists():
        return 0, 0
    d = pd.read_csv(path, dtype=str).fillna("")
    needed = {"cell_id", "reviewer", "reviewer_decision", "review_note"}
    if not needed.issubset(d.columns):
        raise ValueError(f"risk_cells_reviewed.csv missing {sorted(needed-set(d.columns))}")
    active = set(risk_queue["cell_id"])
    d = d[d["cell_id"].isin(active) & (d["reviewer_decision"].str.strip() != "")].copy()
    if d["cell_id"].duplicated().any():
        raise ValueError("Risk cell review must have unique cell_id")
    if (d["reviewer"].str.strip() == "").any():
        raise ValueError("Risk cell decision needs reviewer")
    allowed = {"approve", "reject", "escalate"}
    if not d["reviewer_decision"].str.lower().isin(allowed).all():
        raise ValueError(f"Risk cells decisions must be {sorted(allowed)}")
    for r in d.itertuples(index=False):
        ctx.audit.log(actor=r.reviewer, action=f"risk_cell_review:{r.reviewer_decision}",
                      item_id=r.cell_id, reason=r.review_note)
    approved = int((d["reviewer_decision"].str.lower() == "approve").sum())
    return len(d), approved


# --------------------------------------------------------------- 05 DECIDE
def decide(ctx: RunContext, final: pd.DataFrame, candidates: pd.DataFrame, targets: pd.DataFrame, queue: pd.DataFrame) -> Decision:
    owner = str(ctx.config.get("owner", "")).strip()
    k = int(ctx.param("k", 30))
    if len(final) != k or final["clip_id"].nunique() != k:
        return Decision("REWORK", "INVALID_PICKS", "Pick output must contain K distinct valid clip IDs", owner, ctx.track)
    coverage = coverage_table(final, candidates, targets)
    coverage.to_csv(ctx.out("coverage.csv"), index=False)
    total_weight = float(coverage["weight"].sum())
    covered_weight = float(coverage.loc[coverage["estimated_covered"] == 1, "weight"].sum())
    proxy_coverage = covered_weight / total_weight if total_weight else 0.0
    hard_missing = coverage[(coverage["is_hard"] == 1) & (coverage["estimated_covered"] == 0)]
    missing = coverage[coverage["estimated_covered"] == 0].copy()

    # Capture plan: all missing cells + enough hard cell verification shots to give >=3 proposals.
    proposals = []
    for _, cell in missing.sort_values(["is_hard", "weight"], ascending=[False, False]).iterrows():
        proposals.append((cell, "capture_missing_cell", "No selected clip matches this cell in visible metadata"))
    for _, cell in coverage[(coverage["is_hard"] == 1) & (coverage["estimated_covered"] == 1)].sort_values("weight", ascending=False).iterrows():
        if len(proposals) >= 3:
            break
        proposals.append((cell, "verify_or_recapture_hard_cell", "Metadata coverage is not verified; check visual evidence"))
    capture = []
    for priority, (cell, action, reason) in enumerate(proposals, 1):
        capture.append({"priority": priority, "cell_id": cell["cell_id"], "weight": cell["weight"],
                        "is_hard": int(cell["is_hard"]), "action": action,
                        **{d: cell[d] for d in DIMS}, "reason": reason, "owner": owner})
    pd.DataFrame(capture, columns=["priority", "cell_id", "weight", "is_hard", "action", *DIMS, "reason", "owner"]).to_csv(
        ctx.out("capture_plan.csv"), index=False)
    risk_queue = _create_risk_review_queue(ctx, coverage)
    n_risk_reviewed, n_risk_approved = _risk_review_stats(ctx, risk_queue)
    ctx.stats.update({"proxy_coverage": round(proxy_coverage, 6), "n_missing_cells": len(missing),
                      "hard_missing": hard_missing["cell_id"].tolist(), "n_risk_reviewed": n_risk_reviewed,
                      "n_risk_approved": n_risk_approved})
    with open(ctx.out("proxy_metrics.json"), "w", encoding="utf-8") as f:
        json.dump({"source": "visible planner metadata only; NOT verified ground truth",
                   "k": k, "weighted_coverage_proxy": proxy_coverage,
                   "covered_weight": covered_weight, "total_weight": total_weight,
                   "n_covered_cells": int(coverage["estimated_covered"].sum()),
                   "n_target_cells": len(coverage), "missing_cells": missing["cell_id"].tolist(),
                   "hard_missing_cells": hard_missing["cell_id"].tolist()}, f, indent=2, ensure_ascii=False)

    n_reviewed = int(ctx.stats.get("n_reviewed", 0))
    if n_reviewed < len(queue) or n_risk_reviewed < len(risk_queue):
        status, code, reason = "HOLD", "PENDING_HUMAN_REVIEW", "Clip and/or risk-cell review not completed"
    elif ctx.stats.get("n_escalated", 0) or n_risk_approved < len(risk_queue):
        status, code, reason = "HOLD", "RISK_REVIEW_UNRESOLVED", "Some reviews need escalation or were rejected"
    elif ctx.stats.get("n_pending_new_clips", 0):
        status, code, reason = "HOLD", "REPLACEMENT_NOT_VERIFIED", "Human replacement clips need independent verification"
    elif len(hard_missing) or proxy_coverage < 0.80:
        status, code, reason = "HOLD", "COVERAGE_GAP", "Critical/missing coverage or coverage proxy below locked threshold"
    else:
        status, code, reason = "GO", "POLICY_CHECK_PASSED", "Metadata coverage and human review policy passed; not legal/privacy approval"
    return Decision(status=status, reason_code=code, reason=reason, owner=owner, scope=ctx.track,
                    evidence=[str(ctx.out(n)) for n in ("pick.csv", "coverage.csv", "capture_plan.csv", "review_queue.csv", "risk_cells_review_queue.csv")],
                    metrics={"weighted_coverage_proxy": round(proxy_coverage, 4),
                             "hard_missing_cells": hard_missing["cell_id"].tolist(),
                             "n_reviewed": n_reviewed, "n_risk_reviewed": n_risk_reviewed})


def run(ctx: RunContext) -> None:
    spec = get_track(ctx.track)
    if ctx.track != "t01":
        raise NotImplementedError(f"This PoC implements T01 only, got {ctx.track}")
    data = load(ctx)
    scored = process(ctx, data)
    ctx.audit.log(actor="pipeline", action="selection_created", item_id=ctx.track,
                  after={"k": len(scored), "method": "greedy_weighted_visible_metadata"})
    ctx.stats["n_items"] = len(data["candidates"])
    queue = rank(ctx, scored)
    final = review(ctx, scored, queue, data["candidates"])
    final = final.copy()
    final["rank"] = range(1, len(final) + 1)
    final[spec.pred_columns + [c for c in final.columns if c not in spec.pred_columns]].to_csv(ctx.out(spec.pred_file), index=False)
    decision = decide(ctx, final, data["candidates"], data["targets"], queue)
    write_decision(decision, ctx.out("decision.json"), ctx.out("decision_log.csv"))
