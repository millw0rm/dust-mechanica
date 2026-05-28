from packages.domain.physics.drivetrain import evaluate_drivetrain, topology_id
from packages.domain.schemas.requirements import RequirementInput
from packages.engineering.policy.loader import load_policy
from packages.engineering.validation import normalize_requirement


def _req(*, travel_mm=800, max_speed_mm_s=500, payload_kg=3, duty=0.5):
    return normalize_requirement(
        RequirementInput(
            functional_targets={
                "travel": {"value": travel_mm, "unit": "mm"},
                "max_speed": {"value": max_speed_mm_s, "unit": "mm/s"},
                "payload_mass": {"value": payload_kg, "unit": "kg"},
                "duty_cycle": duty,
            },
            constraints={"max_motor_power_w": 400, "max_total_mass_kg": 8},
        )
    )


def _codes(result):
    return {warning["code"] for warning in result["warnings"]}


def _base_candidate(topology, transmission):
    return {
        "id": f"{topology}-candidate",
        "topology": topology,
        "motor": {"max_rpm": 3000, "rotor_inertia_kgm2": 0.01},
        "drive": {"id": "drive"},
        "transmission": transmission,
        "achievable_speed": 1.0,
        "torque_margin": 0.4,
        "efficiency": 0.9,
        "total_mass": 5.0,
    }


def test_dispatches_topology_names_to_canonical_drivetrain_checks():
    assert topology_id({"topology": "belt-driven-linear-axis"}) == "belt_axis"
    assert topology_id({"topology": "ball-screw-linear-axis"}) == "ball_screw"
    assert topology_id({"topology": "direct-drive-rotary-axis"}) == "direct_drive"


def test_belt_axis_stretch_and_inertia_known_pass_fail_cases():
    thresholds = load_policy("v1").topology_thresholds
    passing = evaluate_drivetrain(
        _base_candidate("belt-driven-linear-axis", {"belt_stiffness_n_per_m": 50000, "ratio": 2.0}),
        _req(payload_kg=2),
        thresholds,
    )
    assert passing["passed"]
    assert "belt_stretch_margin" in passing["margins"]
    assert "risk_belt_stretch_margin_low" not in _codes(passing)

    failing_candidate = _base_candidate("belt-driven-linear-axis", {"belt_stiffness_n_per_m": 5000, "ratio": 0.25})
    failing_candidate["motor"]["rotor_inertia_kgm2"] = 0.0001
    failing = evaluate_drivetrain(failing_candidate, _req(payload_kg=20), thresholds)
    assert not failing["passed"]
    assert "risk_belt_stretch_margin_low" in _codes(failing)
    assert "risk_belt_reflected_inertia_high" in _codes(failing)


def test_ball_screw_critical_speed_buckling_and_efficiency_known_pass_fail_cases():
    thresholds = load_policy("v1").topology_thresholds
    passing = evaluate_drivetrain(
        _base_candidate("ball-screw-linear-axis", {"lead_mm": 20.0, "diameter_mm": 32.0}),
        _req(travel_mm=300, max_speed_mm_s=200, payload_kg=2),
        thresholds,
    )
    assert passing["passed"]
    assert "ball_screw_critical_speed_margin" in passing["margins"]
    assert "risk_screw_critical_speed_low" not in _codes(passing)

    failing = evaluate_drivetrain(
        _base_candidate("ball-screw-linear-axis", {"lead_mm": 5.0, "diameter_mm": 8.0}),
        _req(travel_mm=2000, max_speed_mm_s=1000, payload_kg=50),
        thresholds,
    )
    assert not failing["passed"]
    assert "risk_screw_critical_speed_low" in _codes(failing)
    assert "risk_screw_buckling_margin_low" in _codes(failing)

    inefficient = _base_candidate("ball-screw-linear-axis", {"lead_mm": 20.0, "diameter_mm": 32.0})
    inefficient["efficiency"] = 0.7
    warning = evaluate_drivetrain(inefficient, _req(travel_mm=300, max_speed_mm_s=200, payload_kg=2), thresholds)
    assert warning["passed"]
    assert "risk_screw_efficiency_low" in _codes(warning)


def test_direct_drive_torque_speed_and_duty_known_pass_fail_cases():
    thresholds = load_policy("v1").topology_thresholds
    passing = evaluate_drivetrain(
        _base_candidate("direct-drive-rotary-axis", {"id": "direct"}),
        _req(max_speed_mm_s=500, duty=0.3),
        thresholds,
    )
    assert passing["passed"]
    assert "direct_drive_duty_weighted_margin" in passing["margins"]
    assert "risk_direct_drive_torque_margin_low" not in _codes(passing)

    failing = _base_candidate("direct-drive-rotary-axis", {"id": "direct"})
    failing["torque_margin"] = 0.05
    failing["achievable_speed"] = 0.52
    result = evaluate_drivetrain(failing, _req(max_speed_mm_s=500, duty=0.95), thresholds)
    assert not result["passed"]
    assert "risk_direct_drive_torque_margin_low" in _codes(result)
    assert "risk_direct_drive_duty_margin_low" in _codes(result)
