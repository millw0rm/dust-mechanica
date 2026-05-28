from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from packages.engineering.adapters.artifacts.base import ArtifactStore
from packages.engineering.adapters.artifacts.local import LocalArtifactStore
from packages.engineering.adapters.toolchain.runners.cadquery import CadQueryRunner


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

        for tool_name in self._unique(selected_tools):
            tool_run = runs_by_tool.get(tool_name)
            if tool_run is None:
                executions.append(self._planned_only(tool_name, "No matching tool_run contract exists for this candidate."))
                continue
            if tool_name == "CadQuery":
                executions.append({"tool": tool_name, **CadQueryRunner(self.artifact_store).run(tool_run)})
                continue
            executions.append(self._planned_only(tool_name, "No concrete runner is configured for this tool yet.", tool_run=tool_run))

        artifact_uris = {
            execution["tool"]: execution.get("artifact_uris", {})
            for execution in executions
            if execution.get("artifact_uris")
        }
        status = "succeeded" if executions and all(item["status"] == "succeeded" for item in executions) else "partial"
        if executions and all(item["status"] == "planned_only" for item in executions):
            status = "planned_only"
        return {
            "candidate_id": candidate.get("id"),
            "status": status,
            "selected_tools": self._unique(selected_tools),
            "executions": executions,
            "artifact_uris": artifact_uris,
        }

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
