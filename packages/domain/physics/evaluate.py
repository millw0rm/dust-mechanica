from __future__ import annotations

from packages.domain.physics.controls import evaluate_controls
from packages.domain.physics.drivetrain import evaluate_drivetrain
from packages.domain.physics.models import PhysicsCheck, PhysicsMargins, PhysicsResult, PhysicsRiskFlag, PhysicsWarning
from packages.domain.physics.structural import estimate_beam_structural_response
from packages.domain.physics.thermal import estimate_thermal_response
from packages.engineering.policy.loader import load_policy


def _check_from_payload(payload: dict) -> PhysicsCheck:
    return PhysicsCheck(
        name=payload["name"],
        status=payload["status"],
        passed=payload["passed"],
        margins=payload.get("margins", {}),
        warnings=[PhysicsWarning(**warning) for warning in payload.get("warnings", [])],
    )


def _status_from_checks(checks: list[PhysicsCheck]) -> str:
    if any(not check.passed for check in checks):
        return "fail"
    if any(check.warnings or check.status == "warning" for check in checks):
        return "warning"
    return "pass"


def _risk_flags_from_warnings(warnings: list[PhysicsWarning]) -> list[PhysicsRiskFlag]:
    flags = []
    for warning in warnings:
        if warning.code.startswith("risk_") or warning.severity == "high":
            flags.append(PhysicsRiskFlag(code=warning.code, message=warning.message, severity=warning.severity))
    return flags


def evaluate_candidate_physics(candidate: dict, requirements) -> PhysicsResult:
    policy = load_policy("v1")
    required_speed = float(requirements.functional_targets.max_speed.value)
    achievable_speed = float(candidate["achievable_speed"])
    torque_margin = float(candidate["torque_margin"])
    total_mass = float(candidate["total_mass"])

    drivetrain = _check_from_payload(evaluate_drivetrain(candidate, requirements, policy.topology_thresholds))

    thermal_margins = estimate_thermal_response(
        duty_cycle=float(requirements.functional_targets.duty_cycle),
        required_speed_mps=required_speed,
        achievable_speed_mps=achievable_speed,
        torque_margin=torque_margin,
        motor=candidate.get("motor", {}),
    )
    thermal_warnings = []
    if thermal_margins["estimated_temp_rise_c"] > policy.thermal_limits.max_temp_rise_c:
        thermal_warnings.append(
            PhysicsWarning(
                code="PHYS_THERMAL_TEMP_RISE_HIGH",
                message=f"Estimated temp rise exceeds {policy.thermal_limits.max_temp_rise_c} C",
                severity="high",
            )
        )
    if thermal_margins["thermal_margin"] < policy.thermal_limits.min_thermal_margin:
        thermal_warnings.append(
            PhysicsWarning(
                code="risk_thermal_margin_low",
                message=f"Thermal margin below {policy.thermal_limits.min_thermal_margin}",
                severity="medium",
            )
        )
    thermal_passed = not any(warning.severity == "high" for warning in thermal_warnings)
    thermal = PhysicsCheck(
        name="thermal",
        status="pass" if thermal_passed and not thermal_warnings else ("warning" if thermal_passed else "fail"),
        passed=thermal_passed,
        margins=thermal_margins,
        warnings=thermal_warnings,
    )

    transmission = candidate.get("transmission", {})
    structural_margins = estimate_beam_structural_response(
        support_condition=transmission.get("support_condition", "simply_supported"),
        span_m=float(transmission.get("travel_span_m", requirements.functional_targets.travel.value)),
        payload_kg=float(requirements.functional_targets.payload_mass.value),
        moving_mass_kg=float(transmission.get("moving_mass_estimate_kg", total_mass)),
        acceleration_load_multiplier=float(transmission.get("acceleration_load_multiplier", 1.2)),
        acceleration_mps2=float(transmission.get("acceleration_mps2", 0.0)),
        youngs_modulus_pa=float(transmission.get("youngs_modulus_pa", 69_000_000_000.0)),
        second_moment_area_m4=float(transmission.get("second_moment_area_m4", 8.0e-8)),
        section_modulus_m3=float(transmission.get("section_modulus_m3", 1.4e-6)),
        allowable_deflection_m=float(policy.structural_limits.max_deflection_mm) / 1000.0,
        allowable_stress_pa=float(transmission.get("allowable_stress_pa", 120_000_000.0)),
    )
    rounded_structural_margins = {key: round(value, 4) for key, value in structural_margins.items()}
    structural_warnings = []
    if structural_margins["estimated_max_deflection_mm"] > policy.structural_limits.max_deflection_mm:
        structural_warnings.append(
            PhysicsWarning(
                code="PHYS_STRUCTURAL_DEFLECTION_HIGH",
                message=f"Estimated deflection exceeds {policy.structural_limits.max_deflection_mm} mm limit",
                severity="high",
            )
        )
    if structural_margins["structural_margin"] < policy.structural_limits.min_structural_margin:
        structural_warnings.append(
            PhysicsWarning(
                code="risk_structural_margin_low",
                message=f"Structural margin below {policy.structural_limits.min_structural_margin}",
                severity="high" if structural_margins["structural_margin"] < 0 else "medium",
            )
        )
    if structural_margins["structural_safety_factor_proxy"] < policy.structural_limits.min_structural_safety_factor_proxy:
        structural_warnings.append(
            PhysicsWarning(
                code="risk_structural_safety_low",
                message=f"Structural safety factor proxy below {policy.structural_limits.min_structural_safety_factor_proxy}",
                severity="high",
            )
        )
    structural_passed = not any(warning.severity == "high" for warning in structural_warnings)
    structural = PhysicsCheck(
        name="structural",
        status="pass" if structural_passed and not structural_warnings else ("warning" if structural_passed else "fail"),
        passed=structural_passed,
        margins=rounded_structural_margins,
        warnings=structural_warnings,
    )

    controls = _check_from_payload(evaluate_controls(candidate, requirements))
    checks = [drivetrain, thermal, structural, controls]
    merged_margins = {}
    warnings: list[PhysicsWarning] = []
    for check in checks:
        merged_margins.update(check.margins)
        warnings.extend(check.warnings)

    return PhysicsResult(
        status=_status_from_checks(checks),
        checks=checks,
        margins=PhysicsMargins(**merged_margins),
        warnings=warnings,
        risk_flags=_risk_flags_from_warnings(warnings),
    )
