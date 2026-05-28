from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from packages.engineering.adapters.artifacts.base import ArtifactStore
from packages.engineering.adapters.artifacts.local import LocalArtifactStore
from packages.engineering.adapters.toolchain.runners.cadquery import CadQueryRunner
from packages.engineering.adapters.toolchain.runners.calculix import CalculixCodeAsterRunner
from packages.engineering.adapters.toolchain.runners.freecad import FreeCADRunner
from packages.engineering.adapters.toolchain.runners.openmdao import OpenMDAORunner


@dataclass
class ToolchainExecutionService:
    """Execute selected toolchain runs with configured concrete runners.

    Candidate generation produces `toolchain_results.tool_runs` contracts. This
    service turns those contracts into runner outputs for tools that are wired in
    locally and records plan-only entries for tools that are not executable yet.
    """

    artifact_store: ArtifactStore = field(default_factory=LocalArtifactStore)

    def run_selected_tools(self, *, candidate: dict[str, Any], selected_tools: list[str]) -> dict[str, Any]:
        toolchain_results = candidate.get("toolchain_results") or {}
        tool_runs = toolchain_results.get("tool_runs") or []
        runs_by_tool = {run.get("tool"): run for run in tool_runs if isinstance(run, dict) and run.get("tool")}
        executions = []
        upstream_artifact_uris: dict[str, dict[str, Any]] = {}

        for tool_name in self._unique(selected_tools):
            tool_run = runs_by_tool.get(tool_name)
            if tool_run is None:
                executions.append(self._planned_only(tool_name, "No matching tool_run contract exists for this candidate."))
                continue
            runnable_tool_run = self._with_upstream_artifacts(tool_run, upstream_artifact_uris)
            if tool_name == "CadQuery":
                execution = {"tool": tool_name, **CadQueryRunner(self.artifact_store).run(runnable_tool_run)}
            elif tool_name == "FreeCAD":
                execution = {"tool": tool_name, **FreeCADRunner(self.artifact_store).run(runnable_tool_run)}
            elif tool_name == "CalculiX / Code_Aster":
                execution = {"tool": tool_name, **CalculixCodeAsterRunner(self.artifact_store).run(runnable_tool_run)}
            elif tool_name == "OpenMDAO":
                execution = {"tool": tool_name, **OpenMDAORunner(self.artifact_store).run(runnable_tool_run)}
            else:
                execution = self._planned_only(tool_name, "No concrete runner is configured for this tool yet.", tool_run=tool_run)
            executions.append(execution)
            if execution.get("artifact_uris"):
                upstream_artifact_uris[tool_name] = execution["artifact_uris"]

        artifact_uris = {
            execution["tool"]: execution.get("artifact_uris", {})
            for execution in executions
            if execution.get("artifact_uris")
        }
        status = self._aggregate_status(executions)
        return {
            "candidate_id": candidate.get("id"),
            "status": status,
            "selected_tools": self._unique(selected_tools),
            "executions": executions,
            "artifact_uris": artifact_uris,
        }

    def _with_upstream_artifacts(
        self, tool_run: dict[str, Any], upstream_artifact_uris: dict[str, dict[str, Any]]
    ) -> dict[str, Any]:
        if not upstream_artifact_uris:
            return tool_run
        runnable_tool_run = dict(tool_run)
        feed = dict(runnable_tool_run.get("feed") or {})
        existing = feed.get("upstream_artifact_uris") if isinstance(feed.get("upstream_artifact_uris"), dict) else {}
        feed["upstream_artifact_uris"] = {**existing, **upstream_artifact_uris}
        runnable_tool_run["feed"] = feed
        return runnable_tool_run

    def _aggregate_status(self, executions: list[dict[str, Any]]) -> str:
        if not executions:
            return "partial"
        statuses = [item.get("status") for item in executions]
        if all(status == "succeeded" for status in statuses):
            return "succeeded"
        if all(status == "planned_only" for status in statuses):
            return "planned_only"
        if all(status == "unavailable" for status in statuses):
            return "unavailable"
        if any(status == "failed" for status in statuses):
            return "partial"
        if any(status == "succeeded" for status in statuses):
            return "partial"
        if any(status == "unavailable" for status in statuses):
            return "unavailable"
        return "partial"

    def _planned_only(self, tool_name: str, reason: str, tool_run: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = {
            "tool": tool_name,
            "status": "planned_only",
            "artifact_uris": {},
            "warnings": [reason],
        }
        if tool_run:
            payload["tool_run_status"] = tool_run.get("status")
            payload["input_fingerprint"] = tool_run.get("input_fingerprint") or (tool_run.get("feed") or {}).get("input_fingerprint")
        return payload

    def _unique(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        unique_values = []
        for value in values:
            if value not in seen:
                seen.add(value)
                unique_values.append(value)
        return unique_values
