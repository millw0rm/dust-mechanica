from dataclasses import dataclass


@dataclass
class SimulationAdapterV1:
    def run(self, model_input: dict) -> dict:
        duty = float(model_input.get("duty_cycle", 0.5))
        torque_margin = float(model_input.get("torque_margin", 0.0))
        speed = float(model_input.get("achievable_speed", 0.0))
        max_speed = float(model_input.get("required_speed", speed))
        motion_feasible = speed >= max_speed * 0.97
        torque_ok = torque_margin - (duty * 0.1) >= 0.1
        thermal_index = duty * (1.0 / max(0.1, torque_margin + 0.2))
        thermal_ok = thermal_index <= 3.0
        return {
            "adapter_version": "simulation-v1",
            "status": "pass" if (motion_feasible and torque_ok and thermal_ok) else "fail",
            "checks": {
                "motion_profile_feasible": motion_feasible,
                "torque_speed_margin_valid": torque_ok,
                "thermal_load_sanity": thermal_ok,
            },
            "metrics": {
                "duty_cycle": duty,
                "torque_margin": torque_margin,
                "achievable_speed": speed,
                "required_speed": max_speed,
                "thermal_index": round(thermal_index, 4),
            },
        }
