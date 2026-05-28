from __future__ import annotations


def evaluate(candidate, normalized_req, constants) -> dict:
    speed_req = float(normalized_req.functional_targets.max_speed.value)
    duty = float(normalized_req.functional_targets.duty_cycle)

    speed_margin = (float(candidate.get("achievable_speed", 0.0)) - speed_req) / max(speed_req, 1e-9)
    torque_margin = float(candidate.get("torque_margin", 0.0))
    duty_factor = 1.0 - duty
    weighted_margin = (0.6 * torque_margin) + (0.4 * speed_margin) - (0.2 * (1.0 - duty_factor))

    warnings = []
    if speed_margin < float(constants.get("min_speed_margin", 0.05)):
        warnings.append({"code": "risk_direct_drive_speed_margin_low", "message": "Direct-drive speed margin below threshold", "severity": "medium"})
    if torque_margin < float(constants.get("min_torque_margin", 0.15)):
        warnings.append({"code": "risk_direct_drive_torque_margin_low", "message": "Direct-drive torque margin below threshold", "severity": "high"})
    if weighted_margin < float(constants.get("min_duty_weighted_margin", 0.0)):
        warnings.append({"code": "risk_direct_drive_duty_margin_low", "message": "Duty-weighted torque-speed margin below threshold", "severity": "high"})

    return {
        "margins": {
            "direct_drive_speed_margin": round(speed_margin, 4),
            "direct_drive_torque_margin": round(torque_margin, 4),
            "direct_drive_duty_weighted_margin": round(weighted_margin, 4),
        },
        "warnings": warnings,
    }
