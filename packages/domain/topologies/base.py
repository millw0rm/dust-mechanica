
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class TopologyDecision:
    topology: str
    feasible: bool
    reasons: list[str] = field(default_factory=list)


class TopologyPlugin(Protocol):
    name: str
    family: str

    def feasibility(self, req: Any, catalog: dict) -> TopologyDecision: ...

    def generate_candidates(self, req: Any, catalog: dict) -> list[dict]: ...

    def risk_heuristics(self, candidate: dict, req: Any) -> list[dict]: ...

    def assumptions(self, req: Any) -> dict: ...
