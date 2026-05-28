from packages.catalog.loader import load_catalog
from packages.domain.schemas.candidate import Candidate, Components, Performance, ScoreBreakdown
from packages.domain.schemas.common import Confidence, RiskFlag
from packages.domain.synthesis.generate import generate_belt_axis_candidates
from packages.domain.scoring.score import score_candidate, rank_candidates
from packages.engineering.validation import validate_requirement


def run_generation_pipeline(req):
    v = validate_requirement(req)
    normalized = v["normalized"]
    catalog = load_catalog()
    raw = generate_belt_axis_candidates(normalized, catalog)
    feasible = [r for r in raw if r["feasible"]]
    out = []
    for r in feasible:
        risks = []
        if r["torque_margin"] < 0.15:
            risks.append(RiskFlag(code="LOW_MARGIN", message="Low torque margin", severity="medium"))
        if r["efficiency"] < 0.85:
            risks.append(RiskFlag(code="LOW_EFF", message="Lower-than-target efficiency", severity="low"))
        score = score_candidate(r, normalized.priorities)
        out.append(Candidate(
            id=r["id"],
            components=Components(motor_id=r["motor"]["id"], drive_id=r["drive"]["id"], transmission_id=r["transmission"]["id"]),
            performance=Performance(achievable_speed_mps=r["achievable_speed"], torque_margin=r["torque_margin"], est_efficiency=r["efficiency"], est_total_mass_kg=r["total_mass"]),
            score_breakdown=ScoreBreakdown(**score),
            risk_flags=risks,
            confidence=Confidence(value=0.65, rationale="heuristic week1 placeholder"),
            feasible=True,
        ))
    ranked = rank_candidates([c.model_dump() for c in out])
    return {
        "normalized": normalized,
        "issues": v["issues"],
        "missing": v["missing"],
        "conflicts": v["conflicts"],
        "candidates": ranked,
    }
