from packages.domain.schemas.requirements import RequirementInput
from packages.domain.services.pipeline import run_generation_pipeline


def test_pipeline_returns_ranked_candidates():
    req = RequirementInput(functional_targets={"travel":{"value":800,"unit":"mm"},"max_speed":{"value":1200,"unit":"mm/s"},"payload_mass":{"value":3,"unit":"kg"},"duty_cycle":0.7}, constraints={"max_motor_power_w":400,"max_total_mass_kg":8})
    out = run_generation_pipeline(req)
    assert out["candidates"]
    assert out["candidates"][0]["score_breakdown"]["total"] >= out["candidates"][-1]["score_breakdown"]["total"]


def test_pipeline_candidates_include_physics_summary_shape():
    req = RequirementInput(functional_targets={"travel":{"value":800,"unit":"mm"},"max_speed":{"value":1200,"unit":"mm/s"},"payload_mass":{"value":3,"unit":"kg"},"duty_cycle":0.7}, constraints={"max_motor_power_w":400,"max_total_mass_kg":8})
    out = run_generation_pipeline(req)
    assert out["candidates"]
    for candidate in out["candidates"]:
        physics = candidate["physics_summary"]
        assert set(physics) >= {"status", "checks", "margins", "warnings", "risk_flags"}
        assert candidate["physics_status"] == physics["status"]
        assert candidate["physics_checks"] == physics["checks"]
        assert candidate["physics_margins"] == physics["margins"]
        assert candidate["physics_warnings"] == physics["warnings"]
        assert candidate["physics_risk_flags"] == physics["risk_flags"]
        assert {check["name"] for check in physics["checks"]} == {"structural", "thermal", "drivetrain", "controls"}
