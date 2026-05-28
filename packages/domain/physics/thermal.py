from __future__ import annotations


def estimate_thermal_response(*, duty_cycle: float, required_speed_mps: float, achievable_speed_mps: float, torque_margin: float, motor: dict) -> dict:
    duty = max(0.0, min(1.0, float(duty_cycle)))
    rated_power_w = float(motor.get("power_w", 0.0))
    copper_resistance_ohm = float(motor.get("copper_resistance_ohm", 0.0) or 0.0)
    thermal_resistance_c_per_w = float(motor.get("thermal_resistance_c_per_w", 0.0) or 0.0)
    catalog_loss_fraction = float(motor.get("catalog_loss_fraction", 0.0) or 0.0)

    # fallback proxies when catalog constants are sparse
    if copper_resistance_ohm <= 0.0:
        copper_resistance_ohm = max(0.2, 0.8 / max(0.2, rated_power_w / 100.0))
    if thermal_resistance_c_per_w <= 0.0:
        mass_kg = float(motor.get("mass_kg", 1.0) or 1.0)
        thermal_resistance_c_per_w = max(0.2, 2.8 / max(0.4, mass_kg))
    if catalog_loss_fraction <= 0.0:
        efficiency = float(motor.get("efficiency", 0.85) or 0.85)
        catalog_loss_fraction = max(0.08, min(0.35, 1.0 - efficiency))

    duty_weighted_load = duty * (1.0 / max(0.2, 1.0 + torque_margin))
    speed_ratio = min(1.5, required_speed_mps / max(1e-6, achievable_speed_mps))
    current_proxy_a = max(0.5, (rated_power_w / 48.0) * duty_weighted_load * speed_ratio)
    copper_loss_w = (current_proxy_a ** 2) * copper_resistance_ohm
    core_and_drive_loss_w = rated_power_w * catalog_loss_fraction * duty_weighted_load
    estimated_losses_w = copper_loss_w + core_and_drive_loss_w
    estimated_temp_rise_c = estimated_losses_w * thermal_resistance_c_per_w

    continuous_margin = 1.0 - duty_weighted_load
    intermittent_margin = max(0.0, 1.35 - duty_weighted_load)
    thermal_margin = continuous_margin if duty >= 0.6 else intermittent_margin

    return {
        "duty_weighted_load": round(duty_weighted_load, 4),
        "estimated_losses_w": round(estimated_losses_w, 4),
        "estimated_temp_rise_c": round(estimated_temp_rise_c, 4),
        "continuous_thermal_margin": round(continuous_margin, 4),
        "intermittent_thermal_margin": round(intermittent_margin, 4),
        "thermal_margin": round(thermal_margin, 4),
        "thermal_mode": "continuous" if duty >= 0.6 else "intermittent",
    }
