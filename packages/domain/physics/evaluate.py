from packages.domain.physics.models import PhysicsMargins, PhysicsResult, PhysicsWarnings


def evaluate_candidate_physics(candidate: dict, requirements) -> PhysicsResult:
    required_speed = float(requirements.functional_targets.max_speed.value)
    achievable_speed = float(candidate["achievable_speed"])
    torque_margin = float(candidate["torque_margin"])
    efficiency = float(candidate["efficiency"])
    total_mass = float(candidate["total_mass"])

    speed_headroom_ratio = (achievable_speed / required_speed) - 1.0 if required_speed > 0 else 0.0
    efficiency_margin = efficiency - 0.75
    mass_budget_margin_kg = 12.0 - total_mass

    margins = PhysicsMargins(
        speed_headroom_ratio=round(speed_headroom_ratio, 4),
        torque_margin=round(torque_margin, 4),
        efficiency_margin=round(efficiency_margin, 4),
        mass_budget_margin_kg=round(mass_budget_margin_kg, 4),
    )

    warnings: list[PhysicsWarnings] = []
    if speed_headroom_ratio < 0.05:
        warnings.append(PhysicsWarnings(code="PHYS_SPEED_HEADROOM_LOW", message="Speed headroom below 5%"))
    if torque_margin < 0.15:
        warnings.append(PhysicsWarnings(code="PHYS_TORQUE_MARGIN_LOW", message="Torque margin below 0.15"))
    if efficiency_margin < 0.0:
        warnings.append(PhysicsWarnings(code="PHYS_EFFICIENCY_LOW", message="Efficiency below 0.75"))
    if mass_budget_margin_kg < 0.0:
        warnings.append(PhysicsWarnings(code="PHYS_MASS_OVER_BUDGET", message="Estimated mass exceeds 12kg budget", severity="high"))

    passed = speed_headroom_ratio >= 0.0 and torque_margin >= 0.0
    summary = "pass" if passed and not warnings else ("pass_with_warnings" if passed else "fail")

    return PhysicsResult(passed=passed, summary=summary, margins=margins, warnings=warnings)
