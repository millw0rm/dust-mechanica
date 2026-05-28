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
            return self._failed(
                "CalculixCodeAsterRunner only accepts tool_run contracts for tool='CalculiX / Code_Aster'."
            )

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
                "toolchain",
                fingerprint,
                "calculix-code-aster",
                "margin-report.json",
                report,
            ),
            "solver_deck": self.artifact_store.put_bytes(
                "toolchain",
                fingerprint,
                "calculix-code-aster",
                "loadcase.inp",
                self._solver_deck_bytes(report),
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
            "availability": {
                "available": False,
                "checked": list(self.executable_names),
            },
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

    def _margin_report(self, feed: dict[str, Any], executable: str) -> dict[str, Any]:
        upstream = (
            feed.get("upstream_artifact_uris")
            if isinstance(feed.get("upstream_artifact_uris"), dict)
            else {}
        )
        freecad_artifacts = (
            upstream.get("FreeCAD") if isinstance(upstream.get("FreeCAD"), dict) else {}
        )
        cadquery_artifacts = (
            upstream.get("CadQuery")
            if isinstance(upstream.get("CadQuery"), dict)
            else {}
        )
        geometry = self._geometry_metadata(feed, freecad_artifacts, cadquery_artifacts)
        load_cases = self._load_cases(feed)
        physics = (
            feed.get("physics_margins")
            if isinstance(feed.get("physics_margins"), dict)
            else {}
        )
        performance = (
            feed.get("performance") if isinstance(feed.get("performance"), dict) else {}
        )
        torque_margin = self._number(performance.get("torque_margin"))
        physics_margin_values = [
            value
            for value in (self._number(value) for value in physics.values())
            if value is not None
        ]
        load_case_margins = [
            load_case["margin"]
            for load_case in load_cases
            if load_case.get("margin") is not None
        ]
        candidate_margins = [*physics_margin_values, *load_case_margins]
        if torque_margin is not None:
            candidate_margins.append(torque_margin)
        stress_margin = min(candidate_margins) if candidate_margins else 0.0
        deflection_margin = self._deflection_margin(load_cases, torque_margin)
        warnings = [
            "FEA report is a deterministic handoff summary; replace with parsed solver results after solver execution."
        ]
        if not geometry.get("source_uri"):
            warnings.append(
                "No upstream geometry artifact URI was provided; solver deck records a pending geometry input."
            )
        return {
            "runner_version": self.runner_version,
            "solver_executable": executable,
            "geometry": geometry,
            "geometry_artifacts": {
                "FreeCAD": freecad_artifacts,
                "CadQuery": cadquery_artifacts,
            },
            "load_cases": load_cases,
            "source_margins": {"physics_margins": physics, "performance": performance},
            "margins": {
                "stress_margin": round(float(stress_margin), 4),
                "deflection_margin": round(float(deflection_margin), 4),
                "status": (
                    "pass"
                    if stress_margin >= 0 and deflection_margin >= 0
                    else "review"
                ),
            },
            "warnings": warnings,
        }

    def _geometry_metadata(
        self,
        feed: dict[str, Any],
        freecad_artifacts: dict[str, Any],
        cadquery_artifacts: dict[str, Any],
    ) -> dict[str, Any]:
        source_uri = (
            freecad_artifacts.get("assembly_checks")
            or freecad_artifacts.get("drawing_handoff")
            or cadquery_artifacts.get("step")
            or feed.get("geometry_uri")
            or feed.get("step_uri")
        )
        return {
            "source_uri": source_uri,
            "step_uri": cadquery_artifacts.get("step") or feed.get("step_uri"),
            "assembly_checks_uri": freecad_artifacts.get("assembly_checks"),
            "drawing_handoff_uri": freecad_artifacts.get("drawing_handoff"),
            "topology": feed.get("topology"),
            "components": (
                feed.get("components")
                if isinstance(feed.get("components"), dict)
                else {}
            ),
        }

    def _load_cases(self, feed: dict[str, Any]) -> list[dict[str, Any]]:
        raw_cases = feed.get("load_cases")
        if isinstance(raw_cases, list):
            cases = [case for case in raw_cases if isinstance(case, dict)]
        elif isinstance(raw_cases, dict):
            cases = [raw_cases]
        else:
            cases = []
        if not cases:
            cases = [self._default_load_case(feed)]
        normalized = []
        for index, case in enumerate(cases, start=1):
            force_n = self._number(case.get("force_n") or case.get("load_n"))
            deflection_mm = self._number(
                case.get("deflection_mm") or case.get("max_deflection_mm")
            )
            allowable_deflection_mm = (
                self._number(case.get("allowable_deflection_mm")) or 1.0
            )
            margin = self._number(case.get("margin"))
            if margin is None and deflection_mm is not None:
                margin = allowable_deflection_mm - deflection_mm
            normalized.append(
                {
                    "name": str(case.get("name") or f"load_case_{index}"),
                    "description": str(
                        case.get("description") or "Deterministic load-case handoff"
                    ),
                    "force_n": round(force_n, 4) if force_n is not None else None,
                    "constraint": case.get("constraint") or "fixed_base",
                    "load_direction": case.get("load_direction") or [0.0, 0.0, -1.0],
                    "allowable_deflection_mm": round(allowable_deflection_mm, 4),
                    "estimated_deflection_mm": (
                        round(deflection_mm, 4) if deflection_mm is not None else None
                    ),
                    "margin": round(margin, 4) if margin is not None else None,
                }
            )
        return normalized

    def _default_load_case(self, feed: dict[str, Any]) -> dict[str, Any]:
        performance = (
            feed.get("performance") if isinstance(feed.get("performance"), dict) else {}
        )
        mass_kg = (
            self._number(
                performance.get("payload_mass_kg") or performance.get("total_mass_kg")
            )
            or 1.0
        )
        torque_margin = self._number(performance.get("torque_margin"))
        return {
            "name": "static_payload_gravity",
            "description": "Gravity load derived from available performance metadata.",
            "force_n": mass_kg * 9.80665,
            "allowable_deflection_mm": 1.0,
            "deflection_mm": max(
                0.0, 1.0 - (torque_margin if torque_margin is not None else 0.25)
            ),
            "margin": torque_margin,
        }

    def _deflection_margin(
        self, load_cases: list[dict[str, Any]], torque_margin: float | None
    ) -> float:
        margins = [
            case["margin"] for case in load_cases if case.get("margin") is not None
        ]
        if margins:
            return min(float(margin) for margin in margins)
        return max(0.0, min(1.0, torque_margin if torque_margin is not None else 0.25))

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
