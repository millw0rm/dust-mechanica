from packages.domain.schemas.requirements import RequirementInput
from packages.domain.services.pipeline import run_generation_pipeline


def _req():
    return RequirementInput(functional_targets={"travel":{"value":800,"unit":"mm"},"max_speed":{"value":1200,"unit":"mm/s"},"payload_mass":{"value":3,"unit":"kg"},"duty_cycle":0.7}, constraints={"max_motor_power_w":400,"max_total_mass_kg":8})


def test_explainability_payload_shape():
    out = run_generation_pipeline(_req())
    assert "assumptions" in out
    c = out["candidates"][0]
    assert "raw_metric" in c["score_breakdown"]["efficiency"]


def test_deterministic_ranking_regression_lock():
    out = run_generation_pipeline(_req())
    assert out["candidates"][0]["id"] == "MTR-002-DRV-002-TRN-001"
