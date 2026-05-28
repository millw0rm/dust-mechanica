from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import shutil
from typing import Any

from packages.engineering.adapters.artifacts.base import ArtifactStore

RUNNER_VERSION = "freecad-runner-v1"


@dataclass
class FreeCADRunner:
    """Optional FreeCAD handoff runner gated by local binary availability.

    The runner validates that a FreeCAD command-line executable is present before
    it emits deterministic assembly/check metadata. If FreeCAD is not installed,
    it returns an `unavailable` payload so API callers can surface the missing
    dependency without treating the toolchain run as an exception.
    """

    artifact_store: ArtifactStore
    executable_names: tuple[str, ...] = ("FreeCADCmd", "freecadcmd", "freecad")
    runner_version: str = RUNNER_VERSION

    def run(self, tool_run: dict[str, Any]) -> dict[str, Any]:
        if tool_run.get("tool") != "FreeCAD":
            return self._failed(
                "FreeCADRunner only accepts tool_run contracts for tool='FreeCAD'."
            )

        executable = self._available_executable()
        if executable is None:
            return self._unavailable(
                "FreeCAD command-line executable is not available; install FreeCADCmd/freecadcmd to enable assembly checks."
            )

        feed = tool_run.get("feed") if isinstance(tool_run.get("feed"), dict) else {}
        fingerprint = self._fingerprint(tool_run, feed)
        metadata = self._assembly_metadata(feed, executable)
        artifact_uris = {
            "assembly_checks": self.artifact_store.put_json(
                "toolchain", fingerprint, "freecad", "assembly-checks.json", metadata
            ),
            "drawing_handoff": self.artifact_store.put_json(
                "toolchain",
                fingerprint,
                "freecad",
                "drawing-handoff.json",
                metadata["drawing_handoff"],
            ),
            "macro": self.artifact_store.put_bytes(
                "toolchain",
                fingerprint,
                "freecad",
                "assembly_handoff.FCMacro",
                self._macro_bytes(metadata),
            ),
        }
        return {
            "status": "succeeded",
            "artifact_uris": artifact_uris,
            "warnings": metadata["warnings"],
            "runner_version": self.runner_version,
            "availability": {"available": True, "executable": executable},
            "metadata": {
                "check_count": len(metadata["checks"]),
                "step_uri": metadata.get("step_uri"),
                "drawing_handoff": metadata["drawing_handoff"],
            },
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

    def _assembly_metadata(
        self, feed: dict[str, Any], executable: str
    ) -> dict[str, Any]:
        upstream = (
            feed.get("upstream_artifact_uris")
            if isinstance(feed.get("upstream_artifact_uris"), dict)
            else {}
        )
        cadquery_artifacts = (
            upstream.get("CadQuery")
            if isinstance(upstream.get("CadQuery"), dict)
            else {}
        )
        step_uri = (
            cadquery_artifacts.get("step")
            or feed.get("step_uri")
            or feed.get("geometry_uri")
        )
        stl_uri = cadquery_artifacts.get("stl") or feed.get("stl_uri")
        components = (
            feed.get("components") if isinstance(feed.get("components"), dict) else {}
        )
        envelope = self._first_dict(feed.get("envelope"), feed.get("cad_artifact_ref"))
        warnings = []
        if not step_uri:
            warnings.append(
                "No CadQuery STEP artifact URI was provided; assembly metadata records a pending geometry input."
            )
        drawing_handoff = {
            "source_step_uri": step_uri,
            "reference_stl_uri": stl_uri,
            "assembly_document": "dust_mechanica_assembly.FCStd",
            "drawing_package": "dust_mechanica_techdraw.pdf",
            "views": ["front", "top", "right", "isometric"],
            "formats": ["FCStd", "PDF", "DXF"],
            "title_block": {
                "project": "dust-mechanica",
                "topology": feed.get("topology"),
                "input_fingerprint": feed.get("input_fingerprint"),
            },
            "notes": [
                "Import source STEP into FreeCAD Part workbench.",
                "Attach purchased components using the component map before releasing drawings.",
                "Generate TechDraw sheets from the named views after constraints are verified.",
            ],
        }
        checks = [
            {
                "name": "step_import",
                "status": "ready" if step_uri else "pending",
                "input_uri": step_uri,
            },
            {
                "name": "component_placeholders",
                "status": "ready",
                "component_count": len(components),
            },
            {
                "name": "drawing_handoff",
                "status": "ready",
                "format": "TechDraw-compatible metadata",
            },
        ]
        return {
            "runner_version": self.runner_version,
            "freecad_executable": executable,
            "step_uri": step_uri,
            "stl_uri": stl_uri,
            "envelope": envelope,
            "components": components,
            "checks": checks,
            "drawing_handoff": drawing_handoff,
            "warnings": warnings,
        }

    def _first_dict(self, *values: Any) -> dict[str, Any]:
        for value in values:
            if isinstance(value, dict):
                return value
        return {}

    def _macro_bytes(self, metadata: dict[str, Any]) -> bytes:
        lines = [
            "# Deterministic FreeCAD handoff macro generated by dust-mechanica.",
            f"# STEP input: {metadata.get('step_uri') or 'pending'}",
            "# Open in FreeCAD and replace placeholder checks with project-specific constraints.",
            "import FreeCAD  # noqa: F401",
            "doc = FreeCAD.newDocument('dust_mechanica_assembly')",
            "doc.Label = 'dust-mechanica assembly handoff'",
        ]
        return ("\n".join(lines) + "\n").encode("utf-8")
