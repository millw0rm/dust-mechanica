from packages.domain.physics.models import PhysicsMargins, PhysicsResult, PhysicsWarnings
from packages.domain.physics.checks import belt_axis, ball_screw, direct_drive
from packages.engineering.policy.loader import load_policy


TOPOLOGY_MAP = {
    "belt_axis": belt_axis,
    "belt-driven-linear-axis": belt_axis,
    "ball_screw": ball_screw,
    "ball-screw-linear-axis": ball_screw,
    "direct_drive": direct_drive,
    "direct-drive-rotary-axis": direct_drive,
}


def _topology_id(candidate: dict) -> str | None:
    topology = candidate.get("topology")
    if topology in TOPOLOGY_MAP:
        return topology
    cid = str(candidate.get("id", ""))
    for key in ("belt_axis", "ball_screw", "direct_drive"):
        if cid.startswith(f"{key}-"):
            return key
    return None


def evaluate_candidate_physics(candidate: dict, requirements) -> PhysicsResult:
    policy = load_policy("v1")
    required_speed = float(requirements.functional_targets.max_speed.value)
    achievable_speed = float(candidate["achievable_speed"])
    torque_margin = float(candidate["torque_margin"])
    efficiency = float(candidate["efficiency"])
    total_mass = float(candidate["total_mass"])

    speed_headroom_ratio = (achievable_speed / required_speed) - 1.0 if required_speed > 0 else 0.0
    efficiency_margin = efficiency - 0.75
    mass_budget_margin_kg = 12.0 - total_mass

    merged_margins = {
        "speed_headroom_ratio": round(speed_headroom_ratio, 4),
        "torque_margin": round(torque_margin, 4),
        "efficiency_margin": round(efficiency_margin, 4),
        "mass_budget_margin_kg": round(mass_budget_margin_kg, 4),
    }

    warnings: list[PhysicsWarnings] = []
    if speed_headroom_ratio < 0.05:
        warnings.append(PhysicsWarnings(code="PHYS_SPEED_HEADROOM_LOW", message="Speed headroom below 5%"))
    if torque_margin < 0.15:
        warnings.append(PhysicsWarnings(code="PHYS_TORQUE_MARGIN_LOW", message="Torque margin below 0.15"))
    if efficiency_margin < 0.0:
        warnings.append(PhysicsWarnings(code="PHYS_EFFICIENCY_LOW", message="Efficiency below 0.75"))
    if mass_budget_margin_kg < 0.0:
        warnings.append(PhysicsWarnings(code="PHYS_MASS_OVER_BUDGET", message="Estimated mass exceeds 12kg budget", severity="high"))

    topology_id = _topology_id(candidate)
    if topology_id:
        checker = TOPOLOGY_MAP[topology_id]
        topo_constants = policy.topology_thresholds.get(topology_id, {})
        result = checker.evaluate(candidate, requirements, topo_constants)
        merged_margins.update(result.get("margins", {}))
        warnings.extend(PhysicsWarnings(**w) for w in result.get("warnings", []))

    passed = speed_headroom_ratio >= 0.0 and torque_margin >= 0.0
    summary = "pass" if passed and not warnings else ("pass_with_warnings" if passed else "fail")

    return PhysicsResult(passed=passed, summary=summary, margins=PhysicsMargins(**merged_margins), warnings=warnings)
