from packages.catalog.loader import load_catalog
from packages.catalog.rules import evaluate_sourcing_rules
from packages.domain.schemas.candidate import Candidate, Components, Performance, ScoreBreakdown
from packages.domain.schemas.common import Confidence, RiskFlag
from packages.domain.scoring.score import score_candidate, rank_candidates
from packages.domain.scoring.sensitivity import assess_ranking_robustness
from packages.engineering.policy.loader import load_policy
from packages.engineering.validation import validate_requirement
from packages.domain.topologies.registry import get_topology
from packages.domain.services.topology_selector import select_topologies
from packages.engineering.adapters.simulation.v1 import SimulationAdapterV1
from packages.engineering.adapters.cad.v1 import CADAdapterV1
from packages.domain.physics.evaluate import evaluate_candidate_physics


def compute_confidence(assumption_count: int, low_margin: bool, sparse_data: bool) -> Confidence:
    penalty = (0.1 * assumption_count) + (0.2 if low_margin else 0.0) + (0.15 if sparse_data else 0.0)
    value = max(0.05, min(0.95, 0.9 - penalty))
    return Confidence(value=round(value, 2), rationale=f"penalty={penalty:.2f}; assumptions={assumption_count}; low_margin={low_margin}; sparse_data={sparse_data}")


def run_generation_pipeline(req, *, allowed_topologies=None, excluded_topologies=None, explain_topology_selection=False, sim_enabled=True, cad_enabled=True):
    v = validate_requirement(req)
    normalized = v["normalized"]
    catalog = load_catalog()
    selection = select_topologies(normalized, catalog, allowed_topologies, excluded_topologies)
    out = []
    policy = load_policy("v1")
    assumptions = {}
    topology_stats = {}
    sim = SimulationAdapterV1() if sim_enabled else None
    cad = CADAdapterV1() if cad_enabled else None
    warnings = []
    if not sim_enabled: warnings.append("simulation adapter disabled")
    if not cad_enabled: warnings.append("cad adapter disabled")

    for topology_name in selection["selected"]:
        plugin = get_topology(topology_name)
        raw = plugin.generate_candidates(normalized, catalog)
        feasible = [r for r in raw if r["feasible"]]
        topology_stats[topology_name] = {"generated": len(raw), "feasible": len(feasible), "rejected": len(raw) - len(feasible)}
        assumptions[topology_name] = plugin.assumptions(normalized)
        for r in feasible:
            comp_rules = evaluate_sourcing_rules(r["motor"], allow_eol=False)
            risks = [RiskFlag(**x) for x in plugin.risk_heuristics(r, normalized)]
            for f in comp_rules["flags"]:
                risks.append(RiskFlag(code=f, message=f, severity="high" if "EOL" in f else "medium"))
            if r["achievable_speed"] < normalized.functional_targets.max_speed.value * policy.risk_thresholds.speed_headroom_factor:
                risks.append(RiskFlag(code="SPEED_HEADROOM_LOW", message="Near speed limit", severity="medium"))
            r["lead_time_days"] = r["motor"].get("lead_time_days", 21)
            r["sourcing_risk"] = comp_rules["penalty"]
            physics = evaluate_candidate_physics(
                {
                    "id": r["id"],
                    "topology": r.get("topology"),
                    "motor": r.get("motor", {}),
                    "drive": r.get("drive", {}),
                    "transmission": r.get("transmission", {}),
                    "achievable_speed": r["achievable_speed"],
                    "torque_margin": r["torque_margin"],
                    "efficiency": r["efficiency"],
                    "total_mass": r["total_mass"],
                },
                normalized,
            )
            for w in physics.warnings:
                if str(w.code).startswith("risk_"):
                    risks.append(RiskFlag(code=w.code, message=w.message, severity=w.severity))
            score = score_candidate(r, normalized.priorities, getattr(req, "decision_objective", "balanced"))
            confidence = compute_confidence(1, r["torque_margin"] < 0.2, not r["motor"].get("vendor"))
            sim_sum = sim.run({"duty_cycle": normalized.functional_targets.duty_cycle, "torque_margin": r["torque_margin"], "achievable_speed": r["achievable_speed"], "required_speed": normalized.functional_targets.max_speed.value}) if sim else {"status": "skipped", "warning": "disabled"}
            cad_ref = cad.build({"components": {"motor": r["motor"]["id"], "drive": r["drive"]["id"], "transmission": r["transmission"]["id"]}}) if cad else {"status": "skipped", "warning": "disabled"}
            out.append(Candidate(id=r["id"], components=Components(motor_id=r["motor"]["id"], drive_id=r["drive"]["id"], transmission_id=r["transmission"]["id"]), performance=Performance(achievable_speed_mps=r["achievable_speed"], torque_margin=r["torque_margin"], est_efficiency=r["efficiency"], est_total_mass_kg=r["total_mass"]), score_breakdown=ScoreBreakdown(**score), risk_flags=risks, confidence=confidence, feasible=True, simulation_summary=sim_sum, cad_artifact_ref={"artifact_id": cad_ref.get("artifact_id"), "artifact_uri": cad_ref.get("artifact_uri"), "status": cad_ref.get("status")}, physics_summary=physics.summary, physics_passed=physics.passed, physics_margins=physics.margins.model_dump(), physics_warnings=[w.model_dump() for w in physics.warnings]))
    ranked = rank_candidates([c.model_dump() for c in out])
    robustness = assess_ranking_robustness(ranked, normalized.priorities, bound=policy.weight_perturbation.bound, samples=policy.weight_perturbation.samples)
    for cand in ranked:
        cand["robustness"] = {"level": robustness["level"], "volatility_index": robustness["volatility_index"]}
    return {"normalized": normalized.model_dump(), "issues": v["issues"], "missing": v["missing"], "conflicts": v["conflicts"], "candidates": ranked, "assumptions": assumptions, "policy_version": policy.version, "topology_selection_trace": selection if explain_topology_selection else {}, "topology_candidate_stats": topology_stats, "warnings": warnings}
