
def _dimension(raw, normalized, weight):
    return {
        "raw_metric": round(raw, 4),
        "normalized_metric": round(normalized, 4),
        "applied_weight": round(weight, 4),
        "weighted_contribution": round(normalized * weight, 4),
    }


def _objective_weights(objective: str):
    if objective == "fastest_delivery":
        return {"lead_time": 0.35, "sourcing_risk": 0.25, "cost": 0.1, "fit": 0.3}
    if objective == "lowest_cost":
        return {"lead_time": 0.1, "sourcing_risk": 0.15, "cost": 0.45, "fit": 0.3}
    if objective == "best_reliability_performance":
        return {"lead_time": 0.1, "sourcing_risk": 0.35, "cost": 0.1, "fit": 0.45}
    return {"lead_time": 0.2, "sourcing_risk": 0.2, "cost": 0.25, "fit": 0.35}


def score_candidate(candidate, priorities, objective="balanced", physics_margins=None, structural_limits=None):
    efficiency_raw = candidate["efficiency"]
    cost_raw = candidate["total_cost"]
    compact_raw = candidate["total_mass"]
    perf_raw = candidate["torque_margin"]
    lead_raw = float(candidate.get("lead_time_days", 30))
    source_raw = float(candidate.get("sourcing_risk", 0.3))

    efficiency_n = efficiency_raw
    cost_n = 1.0 / max(1.0, cost_raw / 100.0)
    compact_n = 1.0 / max(1.0, compact_raw)
    perf_n = max(0.0, min(1.0, perf_raw + 0.5))
    fit_n = efficiency_n * priorities.efficiency + compact_n * priorities.compactness + perf_n * priorities.performance_margin
    lead_n = 1.0 / max(1.0, lead_raw / 7.0)
    source_n = max(0.0, min(1.0, 1.0 - source_raw))
    if physics_margins:
        structural_raw = float(physics_margins.get("structural_margin", physics_margins.get("structural_stress_margin", 0.0)))
    else:
        structural_raw = float((structural_limits or {}).get("min_structural_margin", 0.1))
    min_structural_margin = float((structural_limits or {}).get("min_structural_margin", 0.1))
    structural_n = max(0.0, min(1.0, structural_raw / min_structural_margin)) if min_structural_margin > 0 else 1.0

    ow = _objective_weights(objective)
    base_total = fit_n * ow["fit"] + lead_n * ow["lead_time"] + source_n * ow["sourcing_risk"] + cost_n * ow["cost"]
    structural_weight = 0.15
    total = base_total * (1.0 - structural_weight + (structural_weight * structural_n))
    return {
        "total": round(total, 4),
        "efficiency": _dimension(efficiency_raw, efficiency_n, priorities.efficiency),
        "cost": _dimension(cost_raw, cost_n, ow["cost"]),
        "compactness": _dimension(compact_raw, compact_n, priorities.compactness),
        "performance_margin": _dimension(perf_raw, perf_n, priorities.performance_margin),
        "lead_time_impact": _dimension(lead_raw, lead_n, ow["lead_time"]),
        "sourcing_risk": _dimension(source_raw, source_n, ow["sourcing_risk"]),
        "engineering_fit": _dimension(fit_n, fit_n, ow["fit"]),
        "physics_structural_margin": _dimension(structural_raw, structural_n, structural_weight),
    }


def rank_candidates(candidates):
    return sorted(candidates, key=lambda c: c["score_breakdown"]["total"], reverse=True)
