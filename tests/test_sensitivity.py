from packages.domain.schemas.requirements import RequirementInput
from packages.domain.services.pipeline import run_generation_pipeline


def test_sensitivity_robustness_present():
    req = RequirementInput(functional_targets={"travel":{"value":800,"unit":"mm"},"max_speed":{"value":1200,"unit":"mm/s"},"payload_mass":{"value":3,"unit":"kg"},"duty_cycle":0.7}, constraints={"max_motor_power_w":400,"max_total_mass_kg":8})
    out = run_generation_pipeline(req)
    assert out["candidates"][0]["robustness"]["level"] in {"stable", "medium", "unstable"}
