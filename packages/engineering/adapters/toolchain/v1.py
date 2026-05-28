from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from packages.engineering.adapters.artifacts.base import ArtifactStore


@dataclass(frozen=True)
class ToolCapability:
    name: str
    category: str
    role: str
    output_artifacts: tuple[str, ...]
    open_source: bool = True
    maturity: str = "practical"


TOOL_CAPABILITIES: tuple[ToolCapability, ...] = (
    ToolCapability(
        name="FreeCAD",
        category="cad",
        role="Main open-source CAD host for assemblies, macros, TechDraw, and CalculiX-backed studies.",
        output_artifacts=("FCStd", "STEP", "STL", "technical drawings"),
    ),
    ToolCapability(
        name="CadQuery",
        category="scripted_cad",
        role="Python parametric CAD kernel for reproducible mechanical parts and fixtures.",
        output_artifacts=("STEP", "STL", "Python source"),
    ),
    ToolCapability(
        name="cq_gears",
        category="gears",
        role="CadQuery gear generation for spur/helical/bevel gear geometry and trains.",
        output_artifacts=("gear STEP", "gear mesh metadata"),
    ),
    ToolCapability(
        name="OpenSCAD",
        category="parametric_cad",
        role="Fast text-to-parametric CSG experiments, especially for 3D-printable fixtures.",
        output_artifacts=("SCAD", "STL"),
    ),
    ToolCapability(
        name="BESO / FreeCAD Topology Optimization",
        category="optimization",
        role="Lightweight structural member optimization after load cases are known.",
        output_artifacts=("optimized mesh", "mass reduction report"),
    ),
    ToolCapability(
        name="CalculiX / Code_Aster",
        category="fea",
        role="Open-source finite-element validation for stresses, deflection, modal checks, and thermal sanity.",
        output_artifacts=("FEA result files", "margin report"),
    ),
    ToolCapability(
        name="OpenMDAO",
        category="multidisciplinary_optimization",
        role="Coordinate parameter sweeps across motor, transmission, mass, stiffness, and cost objectives.",
        output_artifacts=("optimization trace", "Pareto set"),
    ),
    ToolCapability(
        name="ROS 2 + Gazebo / Ignition",
        category="robotics_simulation",
        role="Motion, controls, robot cell, and factory automation simulation.",
        output_artifacts=("URDF/SDF", "simulation logs", "trajectory KPIs"),
    ),
    ToolCapability(
        name="Blender / Anton-style generative design",
        category="generative_design",
        role="Mesh-based concept generation and visual/digital-twin context around the mechanical design.",
        output_artifacts=("blend", "mesh", "render"),
        maturity="experimental",
    ),
    ToolCapability(
        name="Zoo Text-to-CAD / Text2CAD / DeepCAD research adapters",
        category="text_to_cad",
        role="Optional prompt-to-B-Rep or editable-CAD exploration before deterministic CAD handoff.",
        output_artifacts=("STEP", "candidate CAD source"),
        maturity="experimental",
    ),
)


@dataclass
class OpenSourceToolchainAdapterV1:
    """Plan deterministic handoffs to open-source CAD/simulation/optimization tools.

    The adapter does not shell out to heavyweight CAD/FEA applications. It packages
    the normalized requirement and candidate facts into the exact payloads a runner
    would feed to those tools, then returns expected result contracts and artifact
    references so the API can expose a traceable toolchain plan today.
    """

    adapter_version: str = "toolchain-v1"
    artifact_store: ArtifactStore | None = None

    def run(
        self,
        *,
        normalized: Any,
        candidate: dict,
        simulation_summary: dict | None = None,
        cad_artifact_ref: dict | None = None,
        physics_summary: dict | None = None,
    ) -> dict:
        normalized_payload = (
            normalized.model_dump() if hasattr(normalized, "model_dump") else normalized
        )
        feed = {
            "requirement": normalized_payload,
            "candidate": self._candidate_payload(candidate),
            "simulation_summary": simulation_summary or {},
            "cad_artifact_ref": cad_artifact_ref or {},
            "physics_summary": physics_summary or {},
        }
        fingerprint = self._fingerprint(feed)
        topology = candidate.get("topology", "unknown")
        transmission = candidate.get("transmission", {})
        transmission_kind = (
            transmission.get("kind")
            or transmission.get("type")
            or transmission.get("id", "")
        )

        runs = [
            self._run_contract(
                "CadQuery",
                fingerprint,
                feed,
                "Generate the parametric base model and export a STEP handoff for the selected candidate.",
                priority=1,
            ),
            self._run_contract(
                "FreeCAD",
                fingerprint,
                feed,
                "Open/import the STEP handoff, assemble purchased components, and prepare drawings/macros.",
                priority=2,
            ),
            self._run_contract(
                "CalculiX / Code_Aster",
                fingerprint,
                feed,
                "Validate stress, deflection, thermal, and modal margins using the physics summary as initial loads.",
                priority=3,
            ),
            self._run_contract(
                "OpenMDAO",
                fingerprint,
                feed,
                "Sweep motor/transmission parameters and return Pareto alternatives around score, mass, speed, and risk.",
                priority=4,
            ),
            self._run_contract(
                "ROS 2 + Gazebo / Ignition",
                fingerprint,
                feed,
                "Simulate actuator motion, controls timing, and optional factory-cell integration.",
                priority=5,
            ),
            self._run_contract(
                "OpenSCAD",
                fingerprint,
                feed,
                "Generate quick-printable fixtures, covers, spacers, and simplified mechanism prototypes.",
                priority=6,
            ),
            self._run_contract(
                "BESO / FreeCAD Topology Optimization",
                fingerprint,
                feed,
                "Lightweight plates/brackets after FEA load cases are approved.",
                priority=7,
            ),
        ]

        if self._is_gear_related(topology, transmission_kind):
            runs.insert(
                1,
                self._run_contract(
                    "cq_gears",
                    fingerprint,
                    feed,
                    "Generate gear geometry and mesh metadata for the transmission variant.",
                    priority=2,
                ),
            )
        else:
            runs.append(
                self._run_contract(
                    "cq_gears",
                    fingerprint,
                    feed,
                    "Keep available for future gear-train variants; current candidate is not gear-driven.",
                    priority=8,
                    status="not_applicable",
                )
            )

        runs.extend(
            [
                self._run_contract(
                    "Blender / Anton-style generative design",
                    fingerprint,
                    feed,
                    "Explore mesh concepts or digital-twin context after engineering geometry is stable.",
                    priority=9,
                    status="optional_experimental",
                ),
                self._run_contract(
                    "Zoo Text-to-CAD / Text2CAD / DeepCAD research adapters",
                    fingerprint,
                    feed,
                    "Try text-to-CAD concept generation, then compare against deterministic CadQuery/FreeCAD output.",
                    priority=10,
                    status="optional_experimental",
                ),
            ]
        )

        return {
            "adapter_version": self.adapter_version,
            "status": "planned",
            "input_fingerprint": fingerprint,
            "evaluated_tools": [
                self._capability_payload(tool) for tool in TOOL_CAPABILITIES
            ],
            "tool_runs": runs,
            "handoff_order": [
                run["tool"] for run in sorted(runs, key=lambda item: item["priority"])
            ],
            "result_contract": {
                "primary_outputs": [
                    "cad_artifacts",
                    "simulation_kpis",
                    "optimization_trace",
                    "review_notes",
                ],
                "execution_mode": "plan_only_until_external_runners_are_configured",
                "next_step": "Attach concrete runners for the selected tool_runs and persist returned artifact URIs.",
            },
        }

    def _run_contract(
        self,
        tool_name: str,
        fingerprint: str,
        feed: dict,
        instruction: str,
        *,
        priority: int,
        status: str = "ready_to_feed",
    ) -> dict:
        capability = next(tool for tool in TOOL_CAPABILITIES if tool.name == tool_name)
        slug = self._slug(tool_name)
        run_feed = {
            "input_fingerprint": fingerprint,
            "topology": feed["candidate"].get("topology"),
            "components": feed["candidate"].get("components"),
            "performance": feed["candidate"].get("performance"),
            "constraints": self._requirement_section(feed, "constraints"),
            "envelope": self._requirement_section(feed, "envelope"),
            "load_cases": self._load_cases(feed),
            "design_variables": self._design_variables(feed),
            "cad_artifact_ref": feed.get("cad_artifact_ref", {}),
            "physics_margins": feed.get("physics_summary", {}).get("margins", {}),
        }
        artifact_uris = {
            "directory": f"artifact://toolchain/{fingerprint}/{slug}",
            "feed": self._artifact_uri(fingerprint, slug, "feed.json"),
            "runner_contract": self._artifact_uri(
                fingerprint, slug, "runner-contract.json"
            ),
        }
        contract = {
            "tool": tool_name,
            "category": capability.category,
            "status": status,
            "priority": priority,
            "instruction": instruction,
            "feed": run_feed,
            "expected_outputs": list(capability.output_artifacts),
            "artifact_uri": artifact_uris["directory"],
            "artifact_uris": artifact_uris,
            "open_source": capability.open_source,
            "maturity": capability.maturity,
        }
        if self.artifact_store is not None:
            artifact_uris["feed"] = self.artifact_store.put_json(
                "toolchain", fingerprint, slug, "feed.json", run_feed
            )
            artifact_uris["runner_contract"] = self.artifact_store.put_json(
                "toolchain",
                fingerprint,
                slug,
                "runner-contract.json",
                {
                    key: value
                    for key, value in contract.items()
                    if key != "artifact_uris"
                },
            )
        return contract

    def _requirement_section(self, feed: dict, key: str) -> dict:
        requirement = (
            feed.get("requirement") if isinstance(feed.get("requirement"), dict) else {}
        )
        value = requirement.get(key)
        return value if isinstance(value, dict) else {}

    def _load_cases(self, feed: dict) -> list[dict[str, Any]]:
        physics_summary = (
            feed.get("physics_summary")
            if isinstance(feed.get("physics_summary"), dict)
            else {}
        )
        raw_cases = physics_summary.get("load_cases") or physics_summary.get("loads")
        if isinstance(raw_cases, list):
            return [case for case in raw_cases if isinstance(case, dict)]
        if isinstance(raw_cases, dict):
            return [raw_cases]
        requirement = (
            feed.get("requirement") if isinstance(feed.get("requirement"), dict) else {}
        )
        targets = (
            requirement.get("functional_targets")
            if isinstance(requirement.get("functional_targets"), dict)
            else {}
        )
        payload_mass = self._target_value(targets.get("payload_mass"))
        if payload_mass is None:
            return []
        return [
            {
                "name": "payload_gravity",
                "description": "Static payload load derived from functional targets.",
                "force_n": payload_mass * 9.80665,
                "load_direction": [0.0, 0.0, -1.0],
                "constraint": "fixed_base",
            }
        ]

    def _design_variables(self, feed: dict) -> dict[str, Any]:
        candidate = (
            feed.get("candidate") if isinstance(feed.get("candidate"), dict) else {}
        )
        performance = (
            candidate.get("performance")
            if isinstance(candidate.get("performance"), dict)
            else {}
        )
        return {
            "drive_scale": {"baseline": 1.0, "sweep_factors": [0.85, 1.0, 1.15]},
            "speed_mps": {"baseline": performance.get("achievable_speed_mps")},
            "mass_kg": {"baseline": performance.get("total_mass_kg")},
        }

    def _target_value(self, target: Any) -> float | None:
        if isinstance(target, dict):
            value = target.get("value")
        else:
            value = target
        if isinstance(value, bool):
            return None
        if isinstance(value, (int, float)):
            return float(value)
        return None

    def _artifact_uri(self, fingerprint: str, slug: str, name: str) -> str:
        return f"artifact://toolchain/{fingerprint}/{slug}/{name}"

    def _candidate_payload(self, candidate: dict) -> dict:
        return {
            "id": candidate.get("id"),
            "topology": candidate.get("topology"),
            "components": {
                "motor": candidate.get("motor", {}).get("id"),
                "drive": candidate.get("drive", {}).get("id"),
                "transmission": candidate.get("transmission", {}).get("id"),
            },
            "performance": {
                "achievable_speed_mps": candidate.get("achievable_speed"),
                "torque_margin": candidate.get("torque_margin"),
                "efficiency": candidate.get("efficiency"),
                "total_mass_kg": candidate.get("total_mass"),
            },
        }

    def _capability_payload(self, capability: ToolCapability) -> dict:
        return {
            "name": capability.name,
            "category": capability.category,
            "role": capability.role,
            "output_artifacts": list(capability.output_artifacts),
            "open_source": capability.open_source,
            "maturity": capability.maturity,
        }

    def _fingerprint(self, payload: dict) -> str:
        raw = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]

    def _is_gear_related(self, topology: str, transmission_kind: str) -> bool:
        haystack = f"{topology} {transmission_kind}".lower()
        return "gear" in haystack or "planetary" in haystack

    def _slug(self, value: str) -> str:
        return "".join(char.lower() if char.isalnum() else "-" for char in value).strip(
            "-"
        )
