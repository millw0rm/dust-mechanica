
from packages.catalog.rules import apply_derating
from packages.domain.topologies.base import TopologyDecision


class BallScrewTopology:
    name = "ball-screw-linear-axis"
    family = "ball_screw"

    def feasibility(self, req, catalog):
        ok = req.functional_targets.travel.value <= 2.5
        reasons = [] if ok else ["ball-screw critical speed/stability limit exceeded for requested stroke"]
        return TopologyDecision(topology=self.name, feasible=ok, reasons=reasons)

    def generate_candidates(self, req, catalog):
        out = []
        for screw in catalog.get("screws", []):
            for motor in catalog.get("motors", []):
                for drive in catalog.get("drives", []):
                    lead = screw["lead_mm"] / 1000.0
                    speed = (motor["max_rpm"] / 60.0) * lead
                    torque_available = apply_derating(motor["torque_nm"], req.functional_targets.duty_cycle, self.family)
                    torque_required = max(0.05, req.functional_targets.payload_mass.value * 9.81 * (lead / (6.283 * screw["efficiency"])))
                    feasible = speed >= req.functional_targets.max_speed.value and torque_available >= torque_required
                    out.append({"id": f"{self.family}-{screw['id']}-{motor['id']}-{drive['id']}", "topology": self.name, "motor": motor, "drive": drive, "transmission": screw, "achievable_speed": speed, "torque_margin": (torque_available - torque_required) / torque_required, "torque_required_nm": torque_required, "efficiency": drive["efficiency"] * screw["efficiency"], "total_mass": motor["mass_kg"] + drive["mass_kg"] + screw["mass_kg"], "total_cost": motor["cost"] + drive["cost"] + screw["cost"], "feasible": feasible})
        return out

    def risk_heuristics(self, candidate, req):
        risks = []
        if req.functional_targets.duty_cycle > 0.85:
            risks.append({"code":"LIFECYCLE_WEAR","message":"High duty cycle may accelerate nut wear","severity":"medium"})
        return risks

    def assumptions(self, req):
        return {"selected_topology_rationale":"ball-screw selected for precision/backlash-sensitive linear motion", "derating_assumptions":"continuous duty applies stronger thermal derating", "fallback_defaults_used": ["assumed preloaded nut class C7"]}
