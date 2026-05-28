
def compatible(motor: dict, drive: dict, transmission: dict, req: dict | None = None, topology: str | None = None) -> bool:
    if motor.get("power_w", 0) > drive.get("max_power_w", 1e9):
        return False
    if transmission.get("ratio") and motor.get("torque_nm", 0) * transmission["ratio"] > transmission.get("max_torque_nm", 1e9):
        return False
    if req and motor.get("power_w", 0) > req.constraints.max_motor_power_w:
        return False
    if topology == "ball_screw" and not transmission.get("lead_mm"):
        return False
    return True


def apply_derating(value: float, duty_cycle: float, topology: str | None = None) -> float:
    factor = 1.0
    if duty_cycle > 0.9:
        factor *= 0.85
    elif duty_cycle > 0.75:
        factor *= 0.92
    if topology == "direct_drive":
        factor *= 0.95
    return value * factor
