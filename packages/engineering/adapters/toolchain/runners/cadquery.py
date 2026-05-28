from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from packages.engineering.adapters.artifacts.base import ArtifactStore


RUNNER_VERSION = "cadquery-runner-v1"


@dataclass(frozen=True)
class PlaceholderEnvelope:
    length_mm: float
    width_mm: float
    height_mm: float


@dataclass
class CadQueryRunner:
    """Generate deterministic placeholder CAD artifacts for one CadQuery tool run.

    This runner intentionally produces a minimal parametric handoff from the
    normalized candidate facts in the OpenSourceToolchainAdapterV1 CadQuery
    contract. The placeholder is a simple axis base with one pad per known
    component, exported as STEP/STL bytes into the configured artifact store so
    downstream stages can validate artifact plumbing before full CAD kernels are
    attached.
    """

    artifact_store: ArtifactStore
    runner_version: str = RUNNER_VERSION

    def run(self, tool_run: dict[str, Any]) -> dict[str, Any]:
        if tool_run.get("tool") != "CadQuery":
            return {
                "status": "failed",
                "artifact_uris": {},
                "warnings": ["CadQueryRunner only accepts tool_run contracts for tool='CadQuery'."],
                "runner_version": self.runner_version,
            }

        feed = tool_run.get("feed") or {}
        fingerprint = self._fingerprint(tool_run, feed)
        envelope, envelope_warnings = self._envelope(feed)
        components = self._components(feed)
        model = self._model_payload(envelope, components, feed)

        artifact_uris = {
            "step": self.artifact_store.put_bytes(
                "toolchain",
                fingerprint,
                "cadquery",
                "placeholder.step",
                self._step_bytes(model),
            ),
            "stl": self.artifact_store.put_bytes(
                "toolchain",
                fingerprint,
                "cadquery",
                "placeholder.stl",
                self._stl_bytes(model),
            ),
            "source": self.artifact_store.put_bytes(
                "toolchain",
                fingerprint,
                "cadquery",
                "placeholder_model.py",
                self._source_bytes(model),
            ),
            "manifest": self.artifact_store.put_json(
                "toolchain",
                fingerprint,
                "cadquery",
                "placeholder-manifest.json",
                model,
            ),
        }

        warnings = [
            *envelope_warnings,
            "Generated deterministic placeholder geometry; replace with real CadQuery kernel export before manufacturing.",
        ]
        return {
            "status": "succeeded",
            "artifact_uris": artifact_uris,
            "warnings": warnings,
            "runner_version": self.runner_version,
        }

    def _fingerprint(self, tool_run: dict[str, Any], feed: dict[str, Any]) -> str:
        explicit = feed.get("input_fingerprint") or tool_run.get("input_fingerprint")
        if isinstance(explicit, str) and explicit:
            return explicit
        raw = json.dumps(tool_run, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def _envelope(self, feed: dict[str, Any]) -> tuple[PlaceholderEnvelope, list[str]]:
        warnings: list[str] = []
        candidate = feed.get("candidate") if isinstance(feed.get("candidate"), dict) else {}
        envelope = self._first_dict(feed.get("envelope"), candidate.get("envelope"), feed.get("cad_artifact_ref"))
        dimensions = self._dimension_triplet(envelope)
        if dimensions is None:
            performance = feed.get("performance") if isinstance(feed.get("performance"), dict) else {}
            mass_kg = self._number(performance.get("total_mass_kg") or performance.get("est_total_mass_kg"))
            dimensions = self._default_dimensions(mass_kg)
            warnings.append("Missing envelope dimensions; used mass-scaled placeholder envelope defaults.")
        length, width, height = dimensions
        return PlaceholderEnvelope(
            length_mm=max(length, 10.0),
            width_mm=max(width, 10.0),
            height_mm=max(height, 5.0),
        ), warnings

    def _first_dict(self, *values: Any) -> dict[str, Any]:
        for value in values:
            if isinstance(value, dict):
                return value
        return {}

    def _dimension_triplet(self, envelope: dict[str, Any]) -> tuple[float, float, float] | None:
        candidates = (
            envelope.get("assumed_max_envelope_mm"),
            envelope.get("max_envelope_mm"),
            envelope.get("envelope_mm"),
            envelope.get("bounding_box_mm"),
            envelope.get("dimensions_mm"),
        )
        for value in candidates:
            if isinstance(value, (list, tuple)) and len(value) >= 3:
                parsed = tuple(self._number(part) for part in value[:3])
                if all(part is not None and part > 0 for part in parsed):
                    return parsed  # type: ignore[return-value]
        length = self._number(envelope.get("length_mm") or envelope.get("travel_mm"))
        width = self._number(envelope.get("width_mm"))
        height = self._number(envelope.get("height_mm"))
        if length is not None and width is not None and height is not None:
            return length, width, height
        return None

    def _default_dimensions(self, mass_kg: float | None) -> tuple[float, float, float]:
        scale = max(1.0, min(3.0, (mass_kg or 2.0) / 2.0))
        return 120.0 * scale, 45.0 * scale, 25.0 * scale

    def _number(self, value: Any) -> float | None:
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        return None

    def _components(self, feed: dict[str, Any]) -> dict[str, str]:
        components = feed.get("components") if isinstance(feed.get("components"), dict) else {}
        return {key: str(value) for key, value in components.items() if value not in (None, "")}

    def _model_payload(
        self,
        envelope: PlaceholderEnvelope,
        components: dict[str, str],
        feed: dict[str, Any],
    ) -> dict[str, Any]:
        component_keys = sorted(components)
        pad_count = max(1, len(component_keys))
        pad_spacing = envelope.length_mm / (pad_count + 1)
        pads = [
            {
                "name": key,
                "component_id": components[key],
                "center_mm": [round((index + 1) * pad_spacing, 3), 0.0, round(envelope.height_mm, 3)],
                "size_mm": [
                    round(min(28.0, envelope.length_mm / (pad_count + 2)), 3),
                    round(envelope.width_mm * 0.55, 3),
                    round(max(4.0, envelope.height_mm * 0.18), 3),
                ],
            }
            for index, key in enumerate(component_keys)
        ]
        return {
            "runner_version": self.runner_version,
            "topology": feed.get("topology"),
            "envelope_mm": {
                "length": round(envelope.length_mm, 3),
                "width": round(envelope.width_mm, 3),
                "height": round(envelope.height_mm, 3),
            },
            "components": components,
            "features": {
                "base_block": {
                    "origin_mm": [0.0, round(-envelope.width_mm / 2.0, 3), 0.0],
                    "size_mm": [round(envelope.length_mm, 3), round(envelope.width_mm, 3), round(envelope.height_mm, 3)],
                },
                "component_pads": pads,
            },
        }

    def _step_bytes(self, model: dict[str, Any]) -> bytes:
        dimensions = model["envelope_mm"]
        name = f"DUST_MECHANICA_PLACEHOLDER_{model.get('topology') or 'UNKNOWN'}"
        lines = [
            "ISO-10303-21;",
            "HEADER;",
            "FILE_DESCRIPTION(('Deterministic placeholder exported by CadQueryRunner'),'2;1');",
            f"FILE_NAME('{name}.step','',('dust-mechanica'),('dust-mechanica'),'CadQueryRunner','dust-mechanica','');",
            "FILE_SCHEMA(('CONFIG_CONTROL_DESIGN'));",
            "ENDSEC;",
            "DATA;",
            f"#1=PRODUCT('{name}','Placeholder axis envelope','L={dimensions['length']} W={dimensions['width']} H={dimensions['height']} mm',());",
            "#2=PRODUCT_DEFINITION_FORMATION('1','placeholder geometry formation',#1);",
            "#3=PRODUCT_DEFINITION('design','placeholder exported for toolchain artifact validation',#2,#4);",
            "#4=PRODUCT_DEFINITION_CONTEXT('part definition',#5,'design');",
            "#5=APPLICATION_CONTEXT('mechanical design');",
            f"#6=PROPERTY_DEFINITION('dust_mechanica_placeholder_manifest','{json.dumps(model, sort_keys=True)}',#3);",
            "ENDSEC;",
            "END-ISO-10303-21;",
        ]
        return ("\n".join(lines) + "\n").encode("utf-8")

    def _stl_bytes(self, model: dict[str, Any]) -> bytes:
        dimensions = model["envelope_mm"]
        length = dimensions["length"]
        width = dimensions["width"]
        height = dimensions["height"]
        vertices = [
            (0.0, -width / 2.0, 0.0),
            (length, -width / 2.0, 0.0),
            (length, width / 2.0, 0.0),
            (0.0, width / 2.0, 0.0),
            (0.0, -width / 2.0, height),
            (length, -width / 2.0, height),
            (length, width / 2.0, height),
            (0.0, width / 2.0, height),
        ]
        triangles = [
            (0, 1, 2), (0, 2, 3),
            (4, 6, 5), (4, 7, 6),
            (0, 4, 5), (0, 5, 1),
            (1, 5, 6), (1, 6, 2),
            (2, 6, 7), (2, 7, 3),
            (3, 7, 4), (3, 4, 0),
        ]
        lines = ["solid dust_mechanica_placeholder"]
        for a, b, c in triangles:
            normal = self._normal(vertices[a], vertices[b], vertices[c])
            lines.append(f"  facet normal {normal[0]:.6f} {normal[1]:.6f} {normal[2]:.6f}")
            lines.append("    outer loop")
            for vertex in (vertices[a], vertices[b], vertices[c]):
                lines.append(f"      vertex {vertex[0]:.6f} {vertex[1]:.6f} {vertex[2]:.6f}")
            lines.append("    endloop")
            lines.append("  endfacet")
        lines.append("endsolid dust_mechanica_placeholder")
        return ("\n".join(lines) + "\n").encode("utf-8")

    def _normal(
        self,
        a: tuple[float, float, float],
        b: tuple[float, float, float],
        c: tuple[float, float, float],
    ) -> tuple[float, float, float]:
        ux, uy, uz = b[0] - a[0], b[1] - a[1], b[2] - a[2]
        vx, vy, vz = c[0] - a[0], c[1] - a[1], c[2] - a[2]
        nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
        magnitude = (nx * nx + ny * ny + nz * nz) ** 0.5 or 1.0
        return nx / magnitude, ny / magnitude, nz / magnitude

    def _source_bytes(self, model: dict[str, Any]) -> bytes:
        dimensions = model["envelope_mm"]
        pads = model["features"]["component_pads"]
        lines = [
            "# Placeholder CadQuery source generated by CadQueryRunner.",
            "# Install cadquery and uncomment the import/build calls to regenerate editable geometry.",
            "# import cadquery as cq",
            f"length_mm = {dimensions['length']!r}",
            f"width_mm = {dimensions['width']!r}",
            f"height_mm = {dimensions['height']!r}",
            f"component_pads = {pads!r}",
            "",
            "# base = cq.Workplane('XY').box(length_mm, width_mm, height_mm, centered=(False, True, False))",
            "# for pad in component_pads:",
            "#     sx, sy, sz = pad['size_mm']",
            "#     cx, cy, cz = pad['center_mm']",
            "#     base = base.union(cq.Workplane('XY').box(sx, sy, sz).translate((cx, cy, cz + sz / 2)))",
        ]
        return ("\n".join(lines) + "\n").encode("utf-8")
