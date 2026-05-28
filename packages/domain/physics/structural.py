from __future__ import annotations


def estimate_beam_structural_response(
    *,
    support_condition: str,
    span_m: float,
    payload_kg: float,
    moving_mass_kg: float,
    acceleration_load_multiplier: float,
    youngs_modulus_pa: float,
    second_moment_area_m4: float,
    section_modulus_m3: float,
    allowable_deflection_m: float,
    allowable_stress_pa: float,
) -> dict[str, float]:
    gravity = 9.81
    effective_load_n = max(0.0, (payload_kg + moving_mass_kg) * gravity * max(0.0, acceleration_load_multiplier))

    if support_condition == "cantilever":
        max_deflection_m = (effective_load_n * (span_m**3)) / (3.0 * youngs_modulus_pa * second_moment_area_m4)
        max_bending_moment_nm = effective_load_n * span_m
    else:
        max_deflection_m = (effective_load_n * (span_m**3)) / (48.0 * youngs_modulus_pa * second_moment_area_m4)
        max_bending_moment_nm = (effective_load_n * span_m) / 4.0

    stress_proxy_pa = max_bending_moment_nm / section_modulus_m3
    deflection_margin = (allowable_deflection_m - max_deflection_m) / allowable_deflection_m if allowable_deflection_m > 0 else -1.0
    stress_margin = (allowable_stress_pa - stress_proxy_pa) / allowable_stress_pa if allowable_stress_pa > 0 else -1.0
    safety_factor_proxy = allowable_stress_pa / stress_proxy_pa if stress_proxy_pa > 0 else 999.0

    return {
        "estimated_max_deflection_mm": max_deflection_m * 1000.0,
        "estimated_stress_proxy_mpa": stress_proxy_pa / 1_000_000.0,
        "structural_deflection_margin": deflection_margin,
        "structural_stress_margin": stress_margin,
        "structural_safety_factor_proxy": safety_factor_proxy,
    }
