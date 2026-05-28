from __future__ import annotations


def evaluate(candidate, normalized_req, constants) -> dict:
    payload = float(normalized_req.functional_targets.payload_mass.value)
    required_speed = float(normalized_req.functional_targets.max_speed.value)
    duty = float(normalized_req.functional_targets.duty_cycle)
    transmission = candidate.get("transmission", {})

    span_m = float(normalized_req.functional_targets.travel.value)
    belt_stiffness = float(transmission.get("belt_stiffness_n_per_m", 25000.0))
    drive_force = max(1.0, payload * 9.81)
    stretch_m = drive_force / belt_stiffness
    allowed_stretch_m = span_m * float(constants.get("max_stretch_ratio", 0.002))
    stretch_margin = (allowed_stretch_m - stretch_m) / max(allowed_stretch_m, 1e-9)

    motor_inertia = float(candidate.get("motor", {}).get("rotor_inertia_kgm2", 0.0005))
    reflected_inertia = payload * (0.03 / max(float(transmission.get("ratio", 1.0)), 1e-9)) ** 2
    inertia_ratio = reflected_inertia / max(motor_inertia, 1e-9)
    max_inertia_ratio = float(constants.get("max_reflected_inertia_ratio", 8.0))
    inertia_margin = (max_inertia_ratio - inertia_ratio) / max(max_inertia_ratio, 1e-9)

    warnings = []
    if stretch_margin < float(constants.get("min_stretch_margin", 0.1)):
        warnings.append({"code": "risk_belt_stretch_margin_low", "message": "Belt stretch margin below threshold", "severity": "high"})
    if inertia_margin < float(constants.get("min_inertia_margin", 0.05)):
        warnings.append({"code": "risk_belt_reflected_inertia_high", "message": "Reflected inertia ratio near/above limit", "severity": "medium"})

    return {
        "margins": {
            "belt_stretch_margin": round(stretch_margin, 4),
            "belt_reflected_inertia_margin": round(inertia_margin, 4),
            "belt_required_speed_mps": required_speed,
            "belt_duty_cycle": duty,
        },
        "warnings": warnings,
    }
