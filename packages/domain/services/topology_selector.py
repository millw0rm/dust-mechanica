
from packages.domain.topologies.registry import all_topologies


def select_topologies(req, catalog, allowed_topologies=None, excluded_topologies=None):
    allowed = set(allowed_topologies or all_topologies().keys())
    excluded = set(excluded_topologies or [])
    selected, rejected = [], {}
    for name, plugin in all_topologies().items():
        if name not in allowed:
            rejected[name] = ["not in allowed_topologies"]
            continue
        if name in excluded:
            rejected[name] = ["in excluded_topologies"]
            continue
        decision = plugin.feasibility(req, catalog)
        if decision.feasible:
            selected.append(name)
        else:
            rejected[name] = decision.reasons
    return {"selected": selected, "rejected": rejected}
