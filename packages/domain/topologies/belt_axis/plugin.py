
from packages.catalog.rules import compatible, apply_derating
from packages.domain.topologies.base import TopologyDecision


class BeltAxisTopology:
    name = "belt-driven-linear-axis"
    family = "belt_axis"

    def feasibility(self, req, catalog):
        return TopologyDecision(topology=self.name, feasible=req.functional_targets.travel.value <= 5.0, reasons=[] if req.functional_targets.travel.value <= 5.0 else ["travel too long for reliable belt stiffness"])

    def generate_candidates(self, req, catalog):
        candidates = []
        payload = req.functional_targets.payload_mass.value
        target_speed = req.functional_targets.max_speed.value
        duty = req.functional_targets.duty_cycle
        for m in catalog["motors"]:
            for d in catalog["drives"]:
                for t in catalog["transmissions"]:
                    if t.get("topology") not in (None, self.family):
                        continue
                    if not compatible(m, d, t, req, self.family):
                        continue
                    achievable_speed = (m["max_rpm"] / 60.0) * 0.03 / t["ratio"]
                    torque_available = apply_derating(m["torque_nm"] * t["ratio"], duty, self.family)
                    torque_required = max(0.05, payload * 9.81 * 0.01)
                    motor_torque_required = torque_required / max(t["ratio"], 1e-6)
                    feasible = achievable_speed >= target_speed and torque_available >= torque_required
                    candidates.append({"id": f"{self.family}-{m['id']}-{d['id']}-{t['id']}", "topology": self.name, "motor": m, "drive": d, "transmission": t, "achievable_speed": achievable_speed, "torque_margin": (torque_available - torque_required) / torque_required, "torque_required_nm": motor_torque_required, "output_torque_required_nm": torque_required, "efficiency": d["efficiency"] * t.get("belt_efficiency", 0.9), "total_mass": m["mass_kg"] + d["mass_kg"] + t["mass_kg"], "total_cost": m["cost"] + d["cost"] + t["cost"], "feasible": feasible})
        return candidates

    def risk_heuristics(self, candidate, req):
        out = []
        if candidate["torque_margin"] < 0.2:
            out.append({"code": "LOW_MARGIN", "message": "Near torque limit", "severity": "high"})
        return out

    def assumptions(self, req):
        return {"selected_topology_rationale": "belt topology selected for linear-axis simplicity and catalog availability", "derating_assumptions": "duty-cycle derating applied to torque availability", "fallback_defaults_used": ["max_speed converted to m/s"]}
