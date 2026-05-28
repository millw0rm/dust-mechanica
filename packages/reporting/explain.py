def build_explainability_report(result: dict) -> dict:
    cands=result.get("candidates",[])
    if not cands:
        return {"summary":"no feasible candidates","binding_constraints":[],"alternatives":[]}
    top=cands[0]
    alts=cands[1:4]
    return {
        "winner": {"id": top["id"], "score": top["score_breakdown"]["total"], "why": "highest weighted score"},
        "alternatives": [{"id":c["id"],"lost_by": round(top["score_breakdown"]["total"]-c["score_breakdown"]["total"],4)} for c in alts],
        "binding_constraints": ["torque_margin", "max_speed_headroom"],
        "near_limits": {"torque_margin": top["performance"]["torque_margin"], "speed": top["performance"]["achievable_speed_mps"]},
    }
