from __future__ import annotations

from packages.domain.physics.checks import ball_screw, belt_axis, direct_drive


TOPOLOGY_ALIASES = {
    "belt_axis": "belt_axis",
    "belt-driven-linear-axis": "belt_axis",
    "ball_screw": "ball_screw",
    "ball-screw-linear-axis": "ball_screw",
    "direct_drive": "direct_drive",
    "direct-drive-rotary-axis": "direct_drive",
}

TOPOLOGY_CHECKS = {
    "belt_axis": belt_axis,
    "ball_screw": ball_screw,
    "direct_drive": direct_drive,
}


def topology_id(candidate: dict) -> str | None:
    """Return the canonical topology family used by policy thresholds/checks."""
    topology = candidate.get("topology")
    if topology in TOPOLOGY_ALIASES:
        return TOPOLOGY_ALIASES[topology]
    candidate_id = str(candidate.get("id", ""))
    for key in TOPOLOGY_CHECKS:
        if candidate_id.startswith(f"{key}-"):
            return key
    return None


def evaluate_drivetrain(candidate: dict, requirements, topology_thresholds: dict) -> dict:
    required_speed = float(requirements.functional_targets.max_speed.value)
    achievable_speed = float(candidate["achievable_speed"])
    torque_margin = float(candidate["torque_margin"])
    efficiency = float(candidate["efficiency"])
    total_mass = float(candidate["total_mass"])

    speed_headroom_ratio = (achievable_speed / required_speed) - 1.0 if required_speed > 0 else 0.0
    efficiency_margin = efficiency - 0.75
    mass_budget_margin_kg = 12.0 - total_mass
    margins = {
        "speed_headroom_ratio": round(speed_headroom_ratio, 4),
        "torque_margin": round(torque_margin, 4),
        "efficiency_margin": round(efficiency_margin, 4),
        "mass_budget_margin_kg": round(mass_budget_margin_kg, 4),
    }

    warnings = []
    if speed_headroom_ratio < 0.05:
        warnings.append({"code": "PHYS_SPEED_HEADROOM_LOW", "message": "Speed headroom below 5%", "severity": "medium"})
    if torque_margin < 0.15:
        warnings.append({"code": "PHYS_TORQUE_MARGIN_LOW", "message": "Torque margin below 0.15", "severity": "medium"})
    if efficiency_margin < 0.0:
        warnings.append({"code": "PHYS_EFFICIENCY_LOW", "message": "Efficiency below 0.75", "severity": "medium"})
    if mass_budget_margin_kg < 0.0:
        warnings.append({"code": "PHYS_MASS_OVER_BUDGET", "message": "Estimated mass exceeds 12kg budget", "severity": "high"})

    topo_id = topology_id(candidate)
    if topo_id:
        checker = TOPOLOGY_CHECKS[topo_id]
        result = checker.evaluate(candidate, requirements, topology_thresholds.get(topo_id, {}))
        margins.update(result.get("margins", {}))
        warnings.extend(result.get("warnings", []))

    passed = speed_headroom_ratio >= 0.0 and torque_margin >= 0.0 and not any(w.get("severity") == "high" for w in warnings)
    status = "pass" if passed and not warnings else ("warning" if passed else "fail")
    return {"name": "drivetrain", "status": status, "passed": passed, "margins": margins, "warnings": warnings}
