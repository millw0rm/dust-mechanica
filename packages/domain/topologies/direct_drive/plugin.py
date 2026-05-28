
from packages.catalog.rules import apply_derating
from packages.domain.topologies.base import TopologyDecision


class DirectDriveRotaryTopology:
    name = "direct-drive-rotary-axis"
    family = "direct_drive"

    def feasibility(self, req, catalog):
        ok = req.functional_targets.travel.value <= 6.2832
        return TopologyDecision(topology=self.name, feasible=ok, reasons=[] if ok else ["travel suggests linear use-case instead of rotary"])

    def generate_candidates(self, req, catalog):
        out = []
        for motor in catalog.get("direct_drive_motors", []):
            speed = motor["max_rpm"] / 60.0
            tq = apply_derating(motor["torque_nm"], req.functional_targets.duty_cycle, self.family)
            tq_req = max(0.02, req.functional_targets.payload_mass.value * 0.2)
            out.append({"id": f"{self.family}-{motor['id']}", "topology": self.name, "motor": motor, "drive": {"id":"integrated-drive"}, "transmission": {"id":"direct"}, "achievable_speed": speed, "torque_margin": (tq-tq_req)/tq_req, "efficiency": motor.get("efficiency", 0.93), "total_mass": motor["mass_kg"], "total_cost": motor["cost"], "feasible": speed >= req.functional_targets.max_speed.value and tq >= tq_req})
        return out

    def risk_heuristics(self, candidate, req):
        return [{"code":"THERMAL_LOAD","message":"Direct-drive thermal load concentrated in stator","severity":"medium"}] if req.functional_targets.duty_cycle > 0.8 else []

    def assumptions(self, req):
        return {"selected_topology_rationale":"direct-drive selected for low backlash rotary motion", "derating_assumptions":"motor-only thermal path applied", "fallback_defaults_used":["assumed rigid coupling to payload inertia"]}
