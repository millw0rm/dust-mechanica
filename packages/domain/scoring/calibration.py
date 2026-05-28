from __future__ import annotations
import json
from collections import Counter
from pathlib import Path
from packages.domain.schemas.requirements import RequirementInput
from packages.domain.services.pipeline import run_generation_pipeline


def run_calibration(bench_path="examples/benchmarks/scenarios.json", out_path="artifacts/calibration/latest.json"):
    scenarios=json.loads(Path(bench_path).read_text())
    matches=0
    stabilities=[]
    mismatches=Counter()
    for s in scenarios:
        out=run_generation_pipeline(RequirementInput(**s["requirement"]))
        feasible=bool(out["candidates"])
        exp=s["expected"]["feasible"]
        if feasible==exp:
            matches+=1
        else:
            mismatches["feasible_mismatch"]+=1
        if out["candidates"]:
            stabilities.append(out["candidates"][0].get("robustness",{}).get("volatility_index",0.0))
    report={"scenarios":len(scenarios),"pass_rate":round(matches/max(1,len(scenarios)),4),"ranking_stability":round(1-(sum(stabilities)/max(1,len(stabilities))),4),"major_mismatch_categories":dict(mismatches)}
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(report,indent=2))
    return report


if __name__ == "__main__":
    print(json.dumps(run_calibration(), indent=2))
