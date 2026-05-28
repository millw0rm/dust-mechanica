from packages.domain.scoring.score import score_candidate
from packages.domain.schemas.common import PriorityWeights


def test_best_performance_but_long_lead_time():
    p = PriorityWeights()
    hi_perf = {"efficiency": 0.9, "total_cost": 200, "total_mass": 3, "torque_margin": 0.8, "lead_time_days": 90, "sourcing_risk": 0.1}
    fast = {"efficiency": 0.75, "total_cost": 180, "total_mass": 4, "torque_margin": 0.3, "lead_time_days": 10, "sourcing_risk": 0.2}
    assert score_candidate(hi_perf, p, "best_reliability_performance")["total"] > score_candidate(fast, p, "best_reliability_performance")["total"]


def test_fastest_delivery_but_lower_efficiency():
    p = PriorityWeights()
    slow_eff = {"efficiency": 0.6, "total_cost": 130, "total_mass": 4, "torque_margin": 0.3, "lead_time_days": 5, "sourcing_risk": 0.3}
    high_eff = {"efficiency": 0.9, "total_cost": 130, "total_mass": 4, "torque_margin": 0.3, "lead_time_days": 60, "sourcing_risk": 0.3}
    assert score_candidate(slow_eff, p, "fastest_delivery")["total"] > score_candidate(high_eff, p, "fastest_delivery")["total"]


def test_lowest_cost_but_higher_risk_flags():
    p = PriorityWeights()
    cheap_risky = {"efficiency": 0.8, "total_cost": 60, "total_mass": 4, "torque_margin": 0.3, "lead_time_days": 30, "sourcing_risk": 0.8}
    pricey_safe = {"efficiency": 0.8, "total_cost": 150, "total_mass": 4, "torque_margin": 0.3, "lead_time_days": 30, "sourcing_risk": 0.1}
    assert score_candidate(cheap_risky, p, "lowest_cost")["cost"]["normalized_metric"] > score_candidate(pricey_safe, p, "lowest_cost")["cost"]["normalized_metric"]
