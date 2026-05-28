from packages.catalog.loader import load_catalog
from packages.domain.schemas.candidate import Candidate, Components, Performance, ScoreBreakdown
from packages.domain.schemas.common import Confidence, RiskFlag
from packages.domain.synthesis.generate import generate_belt_axis_candidates
from packages.domain.scoring.score import score_candidate, rank_candidates
from packages.engineering.validation import validate_requirement


def compute_confidence(assumption_count: int, low_margin: bool, sparse_data: bool) -> Confidence:
    penalty = (0.1 * assumption_count) + (0.2 if low_margin else 0.0) + (0.15 if sparse_data else 0.0)
    value = max(0.05, min(0.95, 0.9 - penalty))
    return Confidence(value=round(value, 2), rationale=f"penalty={penalty:.2f}; assumptions={assumption_count}; low_margin={low_margin}; sparse_data={sparse_data}")


def run_generation_pipeline(req):
    v = validate_requirement(req)
    normalized = v["normalized"]
    catalog = load_catalog()
    raw = generate_belt_axis_candidates(normalized, catalog)
    feasible = [r for r in raw if r["feasible"]]
    out = []
    assumptions = {
        "selected_topology_rationale": "belt topology selected for linear-axis simplicity and catalog availability",
        "derating_assumptions": "duty-cycle derating applied to torque availability",
        "fallback_defaults_used": ["max_speed converted to m/s"],
    }
    for r in feasible:
        risks = []
        if r["torque_margin"] < 0.15:
            risks.append(RiskFlag(code="LOW_MARGIN", message="Near torque limit", severity="high"))
        if r["achievable_speed"] < normalized.functional_targets.max_speed.value * 1.05:
            risks.append(RiskFlag(code="SPEED_HEADROOM_LOW", message="Near speed limit", severity="medium"))
        if r["efficiency"] < 0.85:
            risks.append(RiskFlag(code="THERMAL_HEADROOM_LOW", message="Lower efficiency can increase thermal load", severity="medium"))
        if not r["motor"].get("vendor"):
            risks.append(RiskFlag(code="UNCERTAIN_CATALOG_DATA", message="Catalog metadata incomplete", severity="low"))
        score = score_candidate(r, normalized.priorities)
        confidence = compute_confidence(len(assumptions["fallback_defaults_used"]), r["torque_margin"] < 0.2, not r["motor"].get("vendor"))
        out.append(Candidate(
            id=r["id"],
            components=Components(motor_id=r["motor"]["id"], drive_id=r["drive"]["id"], transmission_id=r["transmission"]["id"]),
            performance=Performance(achievable_speed_mps=r["achievable_speed"], torque_margin=r["torque_margin"], est_efficiency=r["efficiency"], est_total_mass_kg=r["total_mass"]),
            score_breakdown=ScoreBreakdown(**score), risk_flags=risks, confidence=confidence, feasible=True,
        ))
    ranked = rank_candidates([c.model_dump() for c in out])
    return {"normalized": normalized.model_dump(), "issues": v["issues"], "missing": v["missing"], "conflicts": v["conflicts"], "candidates": ranked, "assumptions": assumptions}
