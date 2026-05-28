from packages.domain.physics.thermal import estimate_thermal_response


def _motor():
    return {"power_w": 220, "mass_kg": 1.1, "thermal_resistance_c_per_w": 1.6, "copper_resistance_ohm": 0.45, "catalog_loss_fraction": 0.14}


def test_thermal_margin_low_duty_is_higher_than_high_duty():
    low = estimate_thermal_response(duty_cycle=0.2, required_speed_mps=1.2, achievable_speed_mps=1.5, torque_margin=0.25, motor=_motor())
    high = estimate_thermal_response(duty_cycle=0.9, required_speed_mps=1.2, achievable_speed_mps=1.5, torque_margin=0.25, motor=_motor())

    assert low["thermal_margin"] > high["thermal_margin"]
    assert low["estimated_temp_rise_c"] < high["estimated_temp_rise_c"]


def test_thermal_model_has_continuous_and_intermittent_margins():
    out = estimate_thermal_response(duty_cycle=0.7, required_speed_mps=1.0, achievable_speed_mps=1.2, torque_margin=0.15, motor=_motor())
    assert "continuous_thermal_margin" in out
    assert "intermittent_thermal_margin" in out
    assert out["thermal_mode"] == "continuous"


def test_thermal_model_uses_drive_and_explicit_torque_demand():
    out = estimate_thermal_response(
        duty_cycle=0.85,
        required_speed_mps=1.0,
        achievable_speed_mps=1.0,
        torque_margin=0.05,
        motor={
            "power_w": 120,
            "max_rpm": 2500,
            "torque_nm": 0.45,
            "continuous_torque_nm": 0.2,
            "intermittent_torque_nm": 0.45,
            "thermal_resistance_c_per_w": 0.8,
            "catalog_loss_fraction": 0.18,
        },
        drive={"max_power_w": 60, "efficiency": 0.9, "thermal_resistance_c_per_w": 1.4, "quiescent_loss_w": 2.0},
        torque_demand_nm=0.22,
        efficiency=0.82,
    )

    assert out["torque_demand_nm"] == 0.22
    assert out["drive_loss_w"] > 0
    assert out["thermal_margin"] < 0.2
