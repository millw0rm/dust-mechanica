from __future__ import annotations

import math


def _clamp(value: float, lower: float, upper: float) -> float:
    return max(lower, min(upper, value))


def _positive_float(value, default: float) -> float:
    try:
        out = float(value)
    except (TypeError, ValueError):
        return default
    return out if out > 0.0 else default


def estimate_thermal_response(
    *,
    duty_cycle: float,
    required_speed_mps: float,
    achievable_speed_mps: float,
    torque_margin: float,
    motor: dict,
    drive: dict | None = None,
    torque_demand_nm: float | None = None,
    efficiency: float | None = None,
) -> dict:
    """Estimate motor/drive thermal load and margin from sparse catalog metadata.

    The model is intentionally lightweight for early candidate screening. It uses
    catalog continuous/intermittent torque ratings when present, otherwise falls
    back to conservative proxies derived from peak torque and rated power. Losses
    are split into motor copper/speed-dependent losses and drive conversion losses
    so that candidates can be warned before detailed vendor thermal curves exist.
    """

    drive = drive or {}
    duty = _clamp(float(duty_cycle), 0.0, 1.0)
    rated_power_w = _positive_float(motor.get("power_w"), 0.0)
    peak_torque_nm = _positive_float(motor.get("torque_nm"), max(0.05, rated_power_w / 300.0) if rated_power_w else 0.05)
    continuous_torque_nm = _positive_float(
        motor.get("continuous_torque_nm"),
        peak_torque_nm * float(motor.get("continuous_torque_fraction", 0.65) or 0.65),
    )
    intermittent_torque_nm = _positive_float(motor.get("intermittent_torque_nm"), peak_torque_nm)
    max_rpm = _positive_float(motor.get("max_rpm"), 0.0)
    motor_efficiency = _clamp(float(motor.get("efficiency", efficiency or 0.85) or 0.85), 0.05, 0.99)
    drive_efficiency = _clamp(float(drive.get("efficiency", 0.96) or 0.96), 0.05, 0.995)
    system_efficiency = _clamp(float(efficiency if efficiency is not None else motor_efficiency * drive_efficiency), 0.05, 0.995)

    if torque_demand_nm is None:
        # Infer a motor-side demand from the candidate margin when older topology
        # generators do not provide the explicit torque demand.
        torque_demand_nm = intermittent_torque_nm / max(0.05, 1.0 + float(torque_margin))
    torque_demand_nm = _positive_float(torque_demand_nm, 0.0)

    speed_ratio = _clamp(float(required_speed_mps) / max(1e-6, float(achievable_speed_mps)), 0.0, 1.5)
    operating_rpm = max_rpm * speed_ratio
    operating_rad_s = operating_rpm * 2.0 * math.pi / 60.0
    mechanical_output_w = torque_demand_nm * operating_rad_s

    rms_torque_nm = torque_demand_nm * math.sqrt(duty)
    continuous_torque_margin = (continuous_torque_nm - rms_torque_nm) / max(continuous_torque_nm, 1e-6)
    intermittent_torque_margin = (intermittent_torque_nm - torque_demand_nm) / max(intermittent_torque_nm, 1e-6)

    catalog_loss_fraction = float(motor.get("catalog_loss_fraction", 0.0) or 0.0)
    if catalog_loss_fraction <= 0.0:
        catalog_loss_fraction = _clamp((1.0 / motor_efficiency) - 1.0, 0.08, 0.35)
    rated_motor_loss_w = max(rated_power_w * catalog_loss_fraction, mechanical_output_w * ((1.0 / motor_efficiency) - 1.0))
    torque_load_ratio = rms_torque_nm / max(continuous_torque_nm, 1e-6)
    copper_loss_share = _clamp(float(motor.get("copper_loss_share", 0.65) or 0.65), 0.2, 0.9)
    copper_loss_w = rated_motor_loss_w * copper_loss_share * torque_load_ratio**2
    speed_dependent_loss_w = rated_motor_loss_w * (1.0 - copper_loss_share) * speed_ratio * duty
    motor_loss_w = copper_loss_w + speed_dependent_loss_w

    drive_output_w = mechanical_output_w / max(system_efficiency, 1e-6)
    drive_loss_w = drive_output_w * ((1.0 / drive_efficiency) - 1.0) * duty
    drive_loss_w += float(drive.get("quiescent_loss_w", 0.0) or 0.0) * duty
    estimated_losses_w = motor_loss_w + drive_loss_w

    motor_thermal_resistance = _positive_float(
        motor.get("thermal_resistance_c_per_w"),
        max(0.2, 2.8 / max(0.4, float(motor.get("mass_kg", 1.0) or 1.0))),
    )
    drive_thermal_resistance = _positive_float(drive.get("thermal_resistance_c_per_w"), 1.2)
    motor_temp_rise_c = motor_loss_w * motor_thermal_resistance
    drive_temp_rise_c = drive_loss_w * drive_thermal_resistance
    estimated_temp_rise_c = max(motor_temp_rise_c, drive_temp_rise_c)

    allowable_temp_rise_c = _positive_float(motor.get("allowable_temp_rise_c"), 55.0)
    temp_rise_margin = (allowable_temp_rise_c - estimated_temp_rise_c) / allowable_temp_rise_c
    drive_power_margin = (float(drive.get("max_power_w", rated_power_w or 1e9) or 1e9) - drive_output_w) / max(float(drive.get("max_power_w", rated_power_w or 1e9) or 1e9), 1e-6)

    duty_weighted_load = max(rms_torque_nm / max(continuous_torque_nm, 1e-6), drive_output_w / max(float(drive.get("max_power_w", rated_power_w or 1e9) or 1e9), 1e-6))
    thermal_margin = min(continuous_torque_margin, intermittent_torque_margin, temp_rise_margin, drive_power_margin)

    return {
        "duty_weighted_load": round(duty_weighted_load, 4),
        "torque_demand_nm": round(torque_demand_nm, 4),
        "rms_torque_nm": round(rms_torque_nm, 4),
        "continuous_torque_nm": round(continuous_torque_nm, 4),
        "intermittent_torque_nm": round(intermittent_torque_nm, 4),
        "mechanical_output_w": round(mechanical_output_w, 4),
        "motor_loss_w": round(motor_loss_w, 4),
        "drive_loss_w": round(drive_loss_w, 4),
        "estimated_losses_w": round(estimated_losses_w, 4),
        "motor_temp_rise_c": round(motor_temp_rise_c, 4),
        "drive_temp_rise_c": round(drive_temp_rise_c, 4),
        "estimated_temp_rise_c": round(estimated_temp_rise_c, 4),
        "allowable_temp_rise_c": round(allowable_temp_rise_c, 4),
        "continuous_thermal_margin": round(continuous_torque_margin, 4),
        "intermittent_thermal_margin": round(intermittent_torque_margin, 4),
        "temperature_rise_margin": round(temp_rise_margin, 4),
        "drive_power_margin": round(drive_power_margin, 4),
        "thermal_margin": round(thermal_margin, 4),
        "thermal_mode": "continuous" if duty >= 0.6 else "intermittent",
    }
