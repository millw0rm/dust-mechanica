from __future__ import annotations

from dataclasses import dataclass
import hashlib
import importlib.util
import json
from typing import Any

from packages.engineering.adapters.artifacts.base import ArtifactStore

RUNNER_VERSION = "openmdao-runner-v1"


@dataclass
class OpenMDAORunner:
    """Optional OpenMDAO runner for parameter sweeps and Pareto traces."""

    artifact_store: ArtifactStore
    module_name: str = "openmdao"
    runner_version: str = RUNNER_VERSION

    def run(self, tool_run: dict[str, Any]) -> dict[str, Any]:
        if tool_run.get("tool") != "OpenMDAO":
            return self._failed(
                "OpenMDAORunner only accepts tool_run contracts for tool='OpenMDAO'."
            )

        if importlib.util.find_spec(self.module_name) is None:
            return self._unavailable(
                "OpenMDAO Python package is not available; install openmdao to enable parameter sweeps."
            )

        feed = tool_run.get("feed") if isinstance(tool_run.get("feed"), dict) else {}
        fingerprint = self._fingerprint(tool_run, feed)
        trace = self._pareto_trace(feed)
        artifact_uris = {
            "pareto_trace": self.artifact_store.put_json(
                "toolchain", fingerprint, "openmdao", "pareto-trace.json", trace
            ),
            "problem_source": self.artifact_store.put_bytes(
                "toolchain",
                fingerprint,
                "openmdao",
                "sweep_problem.py",
                self._problem_source_bytes(trace),
            ),
        }
        return {
            "status": "succeeded",
            "artifact_uris": artifact_uris,
            "warnings": trace["warnings"],
            "runner_version": self.runner_version,
            "availability": {"available": True, "module": self.module_name},
            "metrics": {"pareto_points": len(trace["pareto_points"])},
        }

    def _unavailable(self, warning: str) -> dict[str, Any]:
        return {
            "status": "unavailable",
            "artifact_uris": {},
            "warnings": [warning],
            "runner_version": self.runner_version,
            "availability": {"available": False, "checked_module": self.module_name},
        }

    def _failed(self, warning: str) -> dict[str, Any]:
        return {
            "status": "failed",
            "artifact_uris": {},
            "warnings": [warning],
            "runner_version": self.runner_version,
        }

    def _fingerprint(self, tool_run: dict[str, Any], feed: dict[str, Any]) -> str:
        explicit = feed.get("input_fingerprint") or tool_run.get("input_fingerprint")
        if isinstance(explicit, str) and explicit:
            return explicit
        raw = json.dumps(tool_run, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def _pareto_trace(self, feed: dict[str, Any]) -> dict[str, Any]:
        performance = (
            feed.get("performance") if isinstance(feed.get("performance"), dict) else {}
        )
        base_speed = self._number(performance.get("achievable_speed_mps")) or 1.0
        base_mass = (
            self._number(
                performance.get("total_mass_kg") or performance.get("est_total_mass_kg")
            )
            or 5.0
        )
        base_efficiency = self._number(performance.get("efficiency")) or 0.75
        base_torque_margin = self._number(performance.get("torque_margin")) or 0.25
        sweep_factors = self._sweep_factors(feed)
        candidates = []
        for factor in sweep_factors:
            mass_penalty = 1.0 + (factor - 1.0) * 0.35
            efficiency = max(0.0, min(1.0, base_efficiency - abs(factor - 1.0) * 0.05))
            risk = abs(factor - 1.0) + max(0.0, factor - 1.0) * max(
                0.0, 0.5 - base_torque_margin
            )
            candidate = {
                "factor": round(factor, 4),
                "speed_mps": round(base_speed * factor, 4),
                "mass_kg": round(base_mass * mass_penalty, 4),
                "efficiency": round(efficiency, 4),
                "torque_margin": round(
                    base_torque_margin - max(0.0, factor - 1.0) * 0.2, 4
                ),
                "risk": round(risk, 4),
            }
            candidate["objective"] = round(
                candidate["speed_mps"] * candidate["efficiency"]
                - candidate["mass_kg"] * 0.05
                - candidate["risk"] * 0.25,
                4,
            )
            candidates.append(candidate)
        pareto_points = self._pareto_front(candidates)
        return {
            "runner_version": self.runner_version,
            "inputs": {
                "performance": performance,
                "design_variables": self._design_variables(feed),
                "constraints": (
                    feed.get("constraints")
                    if isinstance(feed.get("constraints"), dict)
                    else {}
                ),
            },
            "sweep_factors": [round(factor, 4) for factor in sweep_factors],
            "all_points": candidates,
            "pareto_points": pareto_points,
            "warnings": [
                "Pareto trace is a deterministic OpenMDAO handoff summary; replace with a project-specific model for production optimization."
            ],
        }

    def _sweep_factors(self, feed: dict[str, Any]) -> list[float]:
        raw = feed.get("sweep_factors")
        if isinstance(raw, (list, tuple)):
            factors = [self._number(value) for value in raw]
            factors = [value for value in factors if value is not None and value > 0]
            if factors:
                return sorted(set(factors))
        return [0.85, 1.0, 1.15]

    def _design_variables(self, feed: dict[str, Any]) -> dict[str, Any]:
        raw = feed.get("design_variables")
        if isinstance(raw, dict):
            return raw
        return {
            "drive_scale": {
                "baseline": 1.0,
                "sweep_factors": self._sweep_factors(feed),
            },
            "topology": feed.get("topology"),
            "components": (
                feed.get("components")
                if isinstance(feed.get("components"), dict)
                else {}
            ),
        }

    def _pareto_front(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        front = []
        for candidate in candidates:
            dominated = False
            for other in candidates:
                if other is candidate:
                    continue
                no_worse = (
                    other["speed_mps"] >= candidate["speed_mps"]
                    and other["efficiency"] >= candidate["efficiency"]
                    and other["mass_kg"] <= candidate["mass_kg"]
                    and other["risk"] <= candidate["risk"]
                )
                strictly_better = (
                    other["speed_mps"] > candidate["speed_mps"]
                    or other["efficiency"] > candidate["efficiency"]
                    or other["mass_kg"] < candidate["mass_kg"]
                    or other["risk"] < candidate["risk"]
                )
                if no_worse and strictly_better:
                    dominated = True
                    break
            if not dominated:
                front.append(candidate)
        return sorted(
            front, key=lambda item: (-item["objective"], item["mass_kg"], item["risk"])
        )

    def _number(self, value: Any) -> float | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        return None

    def _problem_source_bytes(self, trace: dict[str, Any]) -> bytes:
        lines = [
            "# Deterministic OpenMDAO sweep handoff generated by dust-mechanica.",
            "# Install openmdao and replace this placeholder with explicit components/drivers.",
            f"SWEEP_FACTORS = {trace['sweep_factors']!r}",
            f"BASE_INPUTS = {trace['inputs']!r}",
        ]
        return ("\n".join(lines) + "\n").encode("utf-8")
