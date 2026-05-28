def compatible(motor: dict, drive: dict, transmission: dict, req: dict | None = None) -> bool:
    if motor["power_w"] > drive["max_power_w"]:
        return False
    if motor["torque_nm"] * transmission["ratio"] > transmission["max_torque_nm"]:
        return False
    if req and motor["power_w"] > req.constraints.max_motor_power_w:
        return False
    return True


def apply_derating(value: float, duty_cycle: float) -> float:
    if duty_cycle > 0.9:
        return value * 0.85
    if duty_cycle > 0.75:
        return value * 0.92
    return value
