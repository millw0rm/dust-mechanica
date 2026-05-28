from __future__ import annotations


def evaluate_controls(candidate: dict, requirements) -> dict:
    required_speed = float(requirements.functional_targets.max_speed.value)
    achievable_speed = float(candidate["achievable_speed"])
    torque_margin = float(candidate["torque_margin"])
    duty_cycle = float(requirements.functional_targets.duty_cycle)

    speed_ratio = required_speed / max(achievable_speed, 1e-9)
    motion_profile_margin = 1.0 - speed_ratio
    torque_speed_margin = min(float(candidate.get("torque_margin", 0.0)), motion_profile_margin)
    duty_margin = 1.0 - duty_cycle
    margins = {
        "controls_motion_profile_margin": round(motion_profile_margin, 4),
        "controls_torque_speed_margin": round(torque_speed_margin, 4),
        "controls_duty_margin": round(duty_margin, 4),
    }

    warnings = []
    if motion_profile_margin < 0.0:
        warnings.append({"code": "PHYS_CONTROL_MOTION_PROFILE_INFEASIBLE", "message": "Required speed exceeds achievable speed", "severity": "high"})
    elif motion_profile_margin < 0.05:
        warnings.append({"code": "PHYS_CONTROL_MOTION_PROFILE_TIGHT", "message": "Motion profile speed margin below 5%", "severity": "medium"})
    if torque_margin < 0.0:
        warnings.append({"code": "PHYS_CONTROL_TORQUE_SPEED_INVALID", "message": "Torque-speed margin is negative", "severity": "high"})
    if duty_cycle > 0.9:
        warnings.append({"code": "PHYS_CONTROL_HIGH_DUTY_CYCLE", "message": "Duty cycle leaves little control recovery margin", "severity": "medium"})

    passed = not any(w.get("severity") == "high" for w in warnings)
    status = "pass" if passed and not warnings else ("warning" if passed else "fail")
    return {"name": "controls", "status": status, "passed": passed, "margins": margins, "warnings": warnings}
