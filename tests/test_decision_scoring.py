from packages.domain.scoring.score import score_candidate
from packages.domain.schemas.common import PriorityWeights


def test_decision_objective_biases_score():
    c = {"efficiency": 0.8, "total_cost": 100, "total_mass": 4, "torque_margin": 0.4, "lead_time_days": 10, "sourcing_risk": 0.2}
    fast = score_candidate(c, PriorityWeights(), "fastest_delivery")
    cost = score_candidate(c, PriorityWeights(), "lowest_cost")
    assert fast["lead_time_impact"]["applied_weight"] > cost["lead_time_impact"]["applied_weight"]
