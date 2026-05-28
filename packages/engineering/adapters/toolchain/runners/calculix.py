from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import shutil
from typing import Any

from packages.engineering.adapters.artifacts.base import ArtifactStore


RUNNER_VERSION = "calculix-code-aster-runner-v1"


@dataclass
class CalculixCodeAsterRunner:
    """Optional FEA runner for CalculiX or Code_Aster availability."""

    artifact_store: ArtifactStore
    executable_names: tuple[str, ...] = ("ccx", "run_aster", "as_run")
    runner_version: str = RUNNER_VERSION

    def run(self, tool_run: dict[str, Any]) -> dict[str, Any]:
        if tool_run.get("tool") != "CalculiX / Code_Aster":
            return self._failed("CalculixCodeAsterRunner only accepts tool_run contracts for tool='CalculiX / Code_Aster'.")

        executable = self._available_executable()
        if executable is None:
            return self._unavailable(
                "Neither CalculiX (ccx) nor Code_Aster (run_aster/as_run) is available; install one solver to enable FEA margins."
            )

        feed = tool_run.get("feed") if isinstance(tool_run.get("feed"), dict) else {}
        fingerprint = self._fingerprint(tool_run, feed)
        report = self._margin_report(feed, executable)
        artifact_uris = {
            "margin_report": self.artifact_store.put_json(
                "toolchain", fingerprint, "calculix-code-aster", "margin-report.json", report
            ),
            "solver_deck": self.artifact_store.put_bytes(
                "toolchain", fingerprint, "calculix-code-aster", "loadcase.inp", self._solver_deck_bytes(report)
            ),
        }
        return {
            "status": "succeeded",
            "artifact_uris": artifact_uris,
            "warnings": report["warnings"],
            "runner_version": self.runner_version,
            "availability": {"available": True, "executable": executable},
            "metrics": report["margins"],
        }

    def _available_executable(self) -> str | None:
        for name in self.executable_names:
            path = shutil.which(name)
            if path:
                return path
        return None

    def _unavailable(self, warning: str) -> dict[str, Any]:
        return {
            "status": "unavailable",
            "artifact_uris": {},
            "warnings": [warning],
            "runner_version": self.runner_version,
            "availability": {"available": False, "checked": list(self.executable_names)},
        }

    def _failed(self, warning: str) -> dict[str, Any]:
        return {"status": "failed", "artifact_uris": {}, "warnings": [warning], "runner_version": self.runner_version}

    def _fingerprint(self, tool_run: dict[str, Any], feed: dict[str, Any]) -> str:
        explicit = feed.get("input_fingerprint") or tool_run.get("input_fingerprint")
        if isinstance(explicit, str) and explicit:
            return explicit
        raw = json.dumps(tool_run, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def _margin_report(self, feed: dict[str, Any], executable: str) -> dict[str, Any]:
        upstream = feed.get("upstream_artifact_uris") if isinstance(feed.get("upstream_artifact_uris"), dict) else {}
        geometry = upstream.get("FreeCAD") if isinstance(upstream.get("FreeCAD"), dict) else {}
        physics = feed.get("physics_margins") if isinstance(feed.get("physics_margins"), dict) else {}
        performance = feed.get("performance") if isinstance(feed.get("performance"), dict) else {}
        torque_margin = self._number(performance.get("torque_margin"))
        physics_margin_values = [value for value in (self._number(value) for value in physics.values()) if value is not None]
        governing_margin = min(physics_margin_values) if physics_margin_values else torque_margin
        stress_margin = governing_margin if governing_margin is not None else 0.0
        deflection_margin = max(0.0, min(1.0, (torque_margin if torque_margin is not None else 0.25)))
        warnings = ["FEA report is a deterministic handoff summary; replace with parsed solver results after solver execution."]
        if not geometry:
            warnings.append("No upstream FreeCAD geometry/check artifact URI was provided; solver deck records a pending geometry input.")
        return {
            "runner_version": self.runner_version,
            "solver_executable": executable,
            "geometry_artifacts": geometry,
            "load_cases": {"physics_margins": physics, "performance": performance},
            "margins": {
                "stress_margin": round(float(stress_margin), 4),
                "deflection_margin": round(float(deflection_margin), 4),
                "status": "pass" if stress_margin >= 0 and deflection_margin >= 0 else "review",
            },
            "warnings": warnings,
        }

    def _number(self, value: Any) -> float | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        return None

    def _solver_deck_bytes(self, report: dict[str, Any]) -> bytes:
        lines = [
            "** dust-mechanica deterministic CalculiX/Code_Aster handoff deck",
            f"** solver executable: {report.get('solver_executable')}",
            "*HEADING",
            "Placeholder load case for external FEA runner integration",
            "*END STEP",
        ]
        return ("\n".join(lines) + "\n").encode("utf-8")
