from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from statistics import mean

from packages.engineering.policy.loader import load_policy


@dataclass
class RecalibrationSummary:
    sample_size: int
    min_sample_size: int
    proposed: bool


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def _round4(value: float) -> float:
    return round(float(value), 4)


def _as_bool(value, default: bool = True) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "pass", "passed", "feasible"}:
            return True
        if normalized in {"false", "0", "no", "n", "fail", "failed", "infeasible"}:
            return False
    return default


def _propose_updates(current_policy, feedback_rows: list[dict], benchmark_rows: list[dict]) -> dict:
    # Aggregate outcome signals
    avg_lead_error = mean(abs(float(r.get("lead_time_error_days", 0.0))) for r in feedback_rows)
    avg_risk_error = mean(float(r.get("risk_miss", 0.0)) for r in feedback_rows)
    avg_margin = mean(float(r.get("observed_margin", 0.0)) for r in feedback_rows)
    avg_eff = mean(float(r.get("observed_efficiency", 0.0)) for r in feedback_rows)

    expected_pass_rate = mean(1.0 if _as_bool(b.get("expected_feasible"), True) else 0.0 for b in benchmark_rows)
    observed_pass_rate = mean(1.0 if _as_bool(b.get("observed_feasible"), True) else 0.0 for b in benchmark_rows)
    feasibility_gap = observed_pass_rate - expected_pass_rate

    rt = current_policy.risk_thresholds
    wp = current_policy.weight_perturbation

    # Heuristics are intentionally small-step, bounded, deterministic adjustments.
    lead_error_step = math.ceil(avg_lead_error)
    speed_factor = _clamp(rt.speed_headroom_factor + (lead_error_step / 200.0), 1.0, 1.2)
    min_efficiency = _clamp((rt.min_efficiency * 0.7) + (avg_eff * 0.3) - (avg_risk_error / 137.5), 0.7, 0.95)
    low_margin_high = _clamp((rt.low_margin_high * 0.8) + (avg_margin * 0.2) + (avg_risk_error / 20.0), 0.05, 0.4)
    low_margin_medium = _clamp(max(low_margin_high + 0.02, (rt.low_margin_medium * 0.85) + (avg_margin * 0.15)), 0.08, 0.5)

    bound = wp.bound
    samples = int(_clamp(wp.samples + (len(feedback_rows) // 10), 5, 500))

    return {
        "version": "v2-candidate",
        "risk_thresholds": {
            "low_margin_high": _round4(low_margin_high),
            "low_margin_medium": _round4(low_margin_medium),
            "speed_headroom_factor": _round4(speed_factor),
            "min_efficiency": _round4(min_efficiency),
        },
        "weight_perturbation": {
            "bound": _round4(bound),
            "samples": samples,
        },
        "signals": {
            "avg_lead_time_error_days": _round4(avg_lead_error),
            "avg_risk_miss": _round4(avg_risk_error),
            "avg_observed_margin": _round4(avg_margin),
            "avg_observed_efficiency": _round4(avg_eff),
            "expected_pass_rate": _round4(expected_pass_rate),
            "observed_pass_rate": _round4(observed_pass_rate),
        },
    }


def recalibrate_policy(
    feedback_path: str,
    benchmark_path: str,
    output_dir: str = "artifacts/policy-proposals",
    min_sample_size: int = 20,
) -> dict:
    feedback_rows = json.loads(Path(feedback_path).read_text())
    benchmark_rows = json.loads(Path(benchmark_path).read_text())
    sample_size = len(feedback_rows)

    gate = {
        "status": "pending_human_review",
        "approved": False,
        "approved_by": None,
        "approved_at": None,
        "notes": "Human review required before promoting candidate to active policy.",
    }

    proposal = {
        "meta": {
            "sample_size": sample_size,
            "min_sample_size": min_sample_size,
            "generated_from": {
                "feedback_path": feedback_path,
                "benchmark_path": benchmark_path,
            },
        },
        "review_gate": gate,
    }

    if sample_size < min_sample_size:
        proposal["meta"]["decision"] = "no_op_insufficient_sample"
        proposal["current_policy_version"] = load_policy("v1").version
        proposal["candidate_policy"] = None
    else:
        policy = load_policy("v1")
        proposal["meta"]["decision"] = "candidate_generated"
        proposal["current_policy_version"] = policy.version
        proposal["candidate_policy"] = _propose_updates(policy, feedback_rows, benchmark_rows)

    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "latest.json"
    out_path.write_text(json.dumps(proposal, indent=2))

    return proposal


def promote_recalibrated_policy(proposal_path: str, approver: str, notes: str | None = None) -> dict:
    path = Path(proposal_path)
    proposal = json.loads(path.read_text())
    gate = proposal.get("review_gate", {})
    gate.update({"approved": True, "approved_by": approver, "approved_at": "manual", "status": "approved", "notes": notes or gate.get("notes")})
    proposal["review_gate"] = gate
    path.write_text(json.dumps(proposal, indent=2))

    if not proposal.get("candidate_policy"):
        raise ValueError("No candidate policy to promote")
    v2_dir = Path("packages/engineering/policy/v2")
    v2_dir.mkdir(parents=True, exist_ok=True)
    (v2_dir / "scoring.yaml").write_text(json.dumps(proposal["candidate_policy"], indent=2))
    return proposal
