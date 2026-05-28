# Topology Plugin Guide

Topology plugins implement `TopologyPlugin` contract in `packages/domain/topologies/base.py`.

Required methods:
- `feasibility(req, catalog)`
- `generate_candidates(req, catalog)`
- `risk_heuristics(candidate, req)`
- `assumptions(req)`

Register plugins in `packages/domain/topologies/registry.py`.
