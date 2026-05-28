from copy import deepcopy
from packages.domain.schemas.requirements import RequirementInput
from packages.engineering.units import canonical_unit, normalize_quantity


def normalize_requirement(req: RequirementInput) -> RequirementInput:
    req = deepcopy(req)
    ft = req.functional_targets
    ft.travel.value = normalize_quantity(ft.travel.value, ft.travel.unit, "m")
    ft.travel.unit = canonical_unit("m")
    ft.max_speed.value = normalize_quantity(ft.max_speed.value, ft.max_speed.unit, "m/s")
    ft.max_speed.unit = canonical_unit("m/s")
    ft.payload_mass.value = normalize_quantity(ft.payload_mass.value, ft.payload_mass.unit, "kg")
    ft.payload_mass.unit = canonical_unit("kg")
    return req


def detect_missing_inputs(req: RequirementInput) -> list[str]:
    missing = []
    if req.functional_targets.travel.value <= 0:
        missing.append("functional_targets.travel")
    if req.functional_targets.max_speed.value <= 0:
        missing.append("functional_targets.max_speed")
    if req.constraints.max_motor_power_w <= 0:
        missing.append("constraints.max_motor_power_w")
    return missing


def detect_conflicts(req: RequirementInput) -> list[str]:
    conflicts = []
    speed = req.functional_targets.max_speed.value
    power = req.constraints.max_motor_power_w
    if speed > 2.0 and power < 150:
        conflicts.append("High requested speed with low motor power cap")
    if req.functional_targets.duty_cycle > 0.95 and power < 200:
        conflicts.append("Near-continuous duty cycle with low power budget")
    return conflicts


def validate_requirement(req: RequirementInput) -> dict:
    normalized = normalize_requirement(req)
    issues = []
    if normalized.functional_targets.payload_mass.value < 0:
        issues.append("Payload mass must be non-negative")
    if not (0.0 <= normalized.functional_targets.duty_cycle <= 1.0):
        issues.append("Duty cycle out of bounds")
    missing = detect_missing_inputs(normalized)
    conflicts = detect_conflicts(normalized)
    return {
        "normalized": normalized,
        "issues": issues,
        "missing": missing,
        "conflicts": conflicts,
    }
