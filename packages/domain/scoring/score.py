def _dimension(raw, normalized, weight):
    return {
        "raw_metric": round(raw, 4),
        "normalized_metric": round(normalized, 4),
        "applied_weight": round(weight, 4),
        "weighted_contribution": round(normalized * weight, 4),
    }


def score_candidate(candidate, priorities):
    efficiency_raw = candidate["efficiency"]
    cost_raw = candidate["total_cost"]
    compact_raw = candidate["total_mass"]
    perf_raw = candidate["torque_margin"]

    efficiency_n = efficiency_raw
    cost_n = 1.0 / max(1.0, cost_raw / 100.0)
    compact_n = 1.0 / max(1.0, compact_raw)
    perf_n = max(0.0, min(1.0, perf_raw + 0.5))

    total = efficiency_n * priorities.efficiency + cost_n * priorities.cost + compact_n * priorities.compactness + perf_n * priorities.performance_margin
    return {
        "total": round(total, 4),
        "efficiency": _dimension(efficiency_raw, efficiency_n, priorities.efficiency),
        "cost": _dimension(cost_raw, cost_n, priorities.cost),
        "compactness": _dimension(compact_raw, compact_n, priorities.compactness),
        "performance_margin": _dimension(perf_raw, perf_n, priorities.performance_margin),
    }


def rank_candidates(candidates):
    return sorted(candidates, key=lambda c: c["score_breakdown"]["total"], reverse=True)
