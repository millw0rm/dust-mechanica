from __future__ import annotations
import random
from statistics import mean


def _normalize(weights):
    s=sum(weights.values()) or 1.0
    return {k:v/s for k,v in weights.items()}


def assess_ranking_robustness(candidates, priorities, bound=0.08, samples=25, seed=13):
    random.seed(seed)
    top_ids=[]
    keys=["efficiency","cost","compactness","performance_margin"]
    base={k:getattr(priorities,k) for k in keys}
    for _ in range(samples):
        pert={k:max(0.01,base[k]+random.uniform(-bound,bound)) for k in keys}
        w=_normalize(pert)
        scored=[]
        for c in candidates:
            bd=c["score_breakdown"]
            total=sum(bd[k]["normalized_metric"]*w[k] for k in keys)
            scored.append((round(total,6), c["id"]))
        scored.sort(reverse=True)
        top_ids.append(scored[0][1])
    base_top=candidates[0]["id"] if candidates else None
    agree=sum(1 for t in top_ids if t==base_top)/max(1,len(top_ids))
    volatility=round(1-agree,4)
    level="stable" if volatility<=0.2 else "medium" if volatility<=0.5 else "unstable"
    return {"level":level,"volatility_index":volatility,"top_id_agreement":round(agree,4),"mean_top_occurrence":round(mean([1 if t==base_top else 0 for t in top_ids]) if top_ids else 1.0,4)}
