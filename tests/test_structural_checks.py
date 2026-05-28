from packages.domain.physics.evaluate import evaluate_candidate_physics
from packages.domain.physics.structural import estimate_beam_structural_response
from packages.domain.scoring.score import score_candidate
from packages.domain.schemas.common import PriorityWeights
from packages.domain.schemas.requirements import RequirementInput


def _req(travel_mm=800, payload_kg=3):
    return RequirementInput(
        functional_targets={
            "travel": {"value": travel_mm, "unit": "mm"},
            "max_speed": {"value": 1200, "unit": "mm/s"},
            "payload_mass": {"value": payload_kg, "unit": "kg"},
            "duty_cycle": 0.7,
        },
        constraints={"max_motor_power_w": 400, "max_total_mass_kg": 8},
    )


def test_beam_structural_response_reports_deflection_stress_and_margin():
    result = estimate_beam_structural_response(
        support_condition="simply_supported",
        span_m=0.8,
        payload_kg=3.0,
        moving_mass_kg=2.0,
        acceleration_load_multiplier=1.2,
        youngs_modulus_pa=69_000_000_000.0,
        second_moment_area_m4=8.0e-8,
        section_modulus_m3=1.4e-6,
        allowable_deflection_m=0.0005,
        allowable_stress_pa=120_000_000.0,
    )

    assert result["effective_structural_load_n"] > 0
    assert result["estimated_max_deflection_mm"] > 0
    assert result["estimated_stress_proxy_mpa"] > 0
    assert result["structural_margin"] == min(result["structural_deflection_margin"], result["structural_stress_margin"])


def test_low_structural_margin_becomes_risk_flag_and_score_penalty():
    candidate = {
        "id": "weak-frame",
        "topology": "belt-driven-linear-axis",
        "motor": {"id": "M1"},
        "drive": {"id": "D1"},
        "transmission": {
            "id": "Tweak",
            "support_condition": "cantilever",
            "moving_mass_estimate_kg": 20.0,
            "second_moment_area_m4": 1.0e-9,
            "section_modulus_m3": 1.0e-8,
            "allowable_stress_pa": 10_000_000.0,
        },
        "achievable_speed": 2.0,
        "torque_margin": 0.4,
        "efficiency": 0.9,
        "total_mass": 20.0,
    }

    physics = evaluate_candidate_physics(candidate, _req(travel_mm=1200, payload_kg=10))
    assert "risk_structural_margin_low" in {flag.code for flag in physics.risk_flags}
    assert physics.margins.model_dump()["structural_margin"] < 0

    base = {
        "efficiency": 0.9,
        "total_cost": 100,
        "total_mass": 2,
        "torque_margin": 0.4,
        "lead_time_days": 7,
        "sourcing_risk": 0.1,
    }
    healthy = score_candidate(base, PriorityWeights(), physics_margins={"structural_margin": 0.2}, structural_limits={"min_structural_margin": 0.1})
    weak = score_candidate(base, PriorityWeights(), physics_margins=physics.margins.model_dump(), structural_limits={"min_structural_margin": 0.1})
    assert weak["physics_structural_margin"]["normalized_metric"] == 0
    assert weak["total"] < healthy["total"]
