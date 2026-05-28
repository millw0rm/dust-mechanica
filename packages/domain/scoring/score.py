def score_candidate(candidate, priorities):
    efficiency_s = candidate["efficiency"]
    cost_s = 1.0 / max(1.0, candidate["total_cost"] / 100.0)
    compact_s = 1.0 / max(1.0, candidate["total_mass"])
    perf_s = max(0.0, min(1.0, candidate["torque_margin"] + 0.5))
    total = (
        efficiency_s * priorities.efficiency
        + cost_s * priorities.cost
        + compact_s * priorities.compactness
        + perf_s * priorities.performance_margin
    )
    return {
        "total": round(total, 4),
        "efficiency": round(efficiency_s, 4),
        "cost": round(cost_s, 4),
        "compactness": round(compact_s, 4),
        "performance_margin": round(perf_s, 4),
    }


def rank_candidates(candidates):
    return sorted(candidates, key=lambda c: c["score_breakdown"]["total"], reverse=True)
