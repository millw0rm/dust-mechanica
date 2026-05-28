from packages.catalog.rules import compatible, apply_derating


def generate_belt_axis_candidates(req, catalog):
    candidates = []
    payload = req.functional_targets.payload_mass.value
    target_speed = req.functional_targets.max_speed.value
    duty = req.functional_targets.duty_cycle

    for m in catalog["motors"]:
        for d in catalog["drives"]:
            for t in catalog["transmissions"]:
                if not compatible(m, d, t, req):
                    continue
                achievable_speed = (m["max_rpm"] / 60.0) * 0.03 / t["ratio"]
                torque_available = apply_derating(m["torque_nm"] * t["ratio"], duty)
                torque_required = max(0.05, payload * 9.81 * 0.01)
                feasible = achievable_speed >= target_speed and torque_available >= torque_required
                candidates.append({
                    "id": f"{m['id']}-{d['id']}-{t['id']}",
                    "motor": m,
                    "drive": d,
                    "transmission": t,
                    "achievable_speed": achievable_speed,
                    "torque_margin": (torque_available - torque_required) / torque_required,
                    "efficiency": d["efficiency"] * t["belt_efficiency"],
                    "total_mass": m["mass_kg"] + d["mass_kg"] + t["mass_kg"],
                    "total_cost": m["cost"] + d["cost"] + t["cost"],
                    "feasible": feasible,
                })
    return candidates
