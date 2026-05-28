from __future__ import annotations


def evaluate(candidate, normalized_req, constants) -> dict:
    screw = candidate.get("transmission", {})
    motor = candidate.get("motor", {})
    travel_m = float(normalized_req.functional_targets.travel.value)
    lead_m = float(screw.get("lead_mm", 5.0)) / 1000.0
    rpm = float(motor.get("max_rpm", 0.0))

    critical_rpm = float(constants.get("critical_speed_coeff", 4500.0)) / max(travel_m, 0.1)
    critical_speed_margin = (critical_rpm - rpm) / max(critical_rpm, 1e-9)

    dia_m = float(screw.get("diameter_mm", 16.0)) / 1000.0
    euler_load = float(constants.get("buckling_coeff", 1.5e8)) * (dia_m**4) / max(travel_m**2, 1e-9)
    axial_load = max(1.0, float(normalized_req.functional_targets.payload_mass.value) * 9.81)
    buckling_margin = (euler_load - axial_load) / max(euler_load, 1e-9)

    efficiency = float(candidate.get("efficiency", 0.0))
    min_efficiency = float(constants.get("min_efficiency", 0.75))
    efficiency_margin = (efficiency - min_efficiency) / max(min_efficiency, 1e-9)

    warnings = []
    if critical_speed_margin < float(constants.get("min_critical_speed_margin", 0.1)):
        warnings.append({"code": "risk_ball_screw_critical_speed_low", "message": "Ball screw critical speed margin below threshold", "severity": "high"})
    if buckling_margin < float(constants.get("min_buckling_margin", 0.2)):
        warnings.append({"code": "risk_ball_screw_buckling_margin_low", "message": "Buckling margin below threshold", "severity": "high"})
    if efficiency_margin < float(constants.get("min_efficiency_margin", 0.0)):
        warnings.append({"code": "risk_ball_screw_efficiency_low", "message": "Efficiency/losses proxy below threshold", "severity": "medium"})

    return {
        "margins": {
            "ball_screw_critical_speed_margin": round(critical_speed_margin, 4),
            "ball_screw_buckling_margin": round(buckling_margin, 4),
            "ball_screw_efficiency_margin": round(efficiency_margin, 4),
            "ball_screw_lead_m": round(lead_m, 6),
        },
        "warnings": warnings,
    }
