from __future__ import annotations


def _positive(value: float, fallback: float) -> float:
    return value if value > 0 else fallback


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
    acceleration_mps2: float = 0.0,
) -> dict[str, float]:
    """Estimate first-order beam deflection and bending stress for an axis/frame span.

    The check intentionally uses conservative closed-form point-load beam equations so it
    can run during candidate generation without requiring a full FEA model.  The moving
    carriage, payload, and acceleration load are treated as an equivalent center-span
    point load for simply/fixed-supported spans or an end load for cantilever spans.
    """

    gravity_mps2 = 9.81
    span_m = _positive(span_m, 1e-9)
    youngs_modulus_pa = _positive(youngs_modulus_pa, 1e-9)
    second_moment_area_m4 = _positive(second_moment_area_m4, 1e-18)
    section_modulus_m3 = _positive(section_modulus_m3, 1e-18)

    supported_mass_kg = max(0.0, payload_kg) + max(0.0, moving_mass_kg)
    equivalent_acceleration_mps2 = (gravity_mps2 * max(0.0, acceleration_load_multiplier)) + abs(acceleration_mps2)
    effective_load_n = supported_mass_kg * equivalent_acceleration_mps2

    normalized_support = support_condition.lower().replace("-", "_").replace(" ", "_")
    if normalized_support == "cantilever":
        # End point load on a cantilever: delta = P L^3 / 3 E I; Mmax = P L.
        max_deflection_m = (effective_load_n * (span_m**3)) / (3.0 * youngs_modulus_pa * second_moment_area_m4)
        max_bending_moment_nm = effective_load_n * span_m
    elif normalized_support in {"fixed_fixed", "fixed", "both_ends_fixed"}:
        # Center point load with both ends fixed: delta = P L^3 / 192 E I; Mmax = P L / 8.
        max_deflection_m = (effective_load_n * (span_m**3)) / (192.0 * youngs_modulus_pa * second_moment_area_m4)
        max_bending_moment_nm = (effective_load_n * span_m) / 8.0
    else:
        # Center point load on a simply supported beam: delta = P L^3 / 48 E I; Mmax = P L / 4.
        max_deflection_m = (effective_load_n * (span_m**3)) / (48.0 * youngs_modulus_pa * second_moment_area_m4)
        max_bending_moment_nm = (effective_load_n * span_m) / 4.0

    stress_proxy_pa = max_bending_moment_nm / section_modulus_m3
    deflection_margin = (allowable_deflection_m - max_deflection_m) / allowable_deflection_m if allowable_deflection_m > 0 else -1.0
    stress_margin = (allowable_stress_pa - stress_proxy_pa) / allowable_stress_pa if allowable_stress_pa > 0 else -1.0
    safety_factor_proxy = allowable_stress_pa / stress_proxy_pa if stress_proxy_pa > 0 else 999.0
    structural_margin = min(deflection_margin, stress_margin)

    return {
        "effective_structural_load_n": effective_load_n,
        "estimated_max_deflection_mm": max_deflection_m * 1000.0,
        "estimated_stress_proxy_mpa": stress_proxy_pa / 1_000_000.0,
        "structural_deflection_margin": deflection_margin,
        "structural_stress_margin": stress_margin,
        "structural_margin": structural_margin,
        "structural_safety_factor_proxy": safety_factor_proxy,
    }
