from packages.domain.schemas.requirements import RequirementInput
from packages.engineering.validation import validate_requirement


def test_validation_missing_and_conflict():
    req = RequirementInput(functional_targets={"travel":{"value":100,"unit":"mm"},"max_speed":{"value":3000,"unit":"mm/s"},"payload_mass":{"value":1,"unit":"kg"},"duty_cycle":0.5}, constraints={"max_motor_power_w":100,"max_total_mass_kg":5})
    res = validate_requirement(req)
    assert "High requested speed with low motor power cap" in res["conflicts"]
