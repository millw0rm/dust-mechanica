from packages.engineering.adapters.simulation.v1 import SimulationAdapterV1


def test_simulation_adapter_pass_fail():
    a = SimulationAdapterV1()
    ok = a.run({"duty_cycle": 0.5, "torque_margin": 0.5, "achievable_speed": 100, "required_speed": 95})
    bad = a.run({"duty_cycle": 0.95, "torque_margin": 0.05, "achievable_speed": 50, "required_speed": 100})
    assert ok["status"] == "pass"
    assert bad["status"] == "fail"
