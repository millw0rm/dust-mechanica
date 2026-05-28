# Open-source AI/CAD toolchain handoff

Dust Mechanica can now return a deterministic `toolchain_results` plan for each generated candidate. The plan is meant to answer: "what should we feed to the open-source CAD, simulation, optimization, and factory-planning tools, and what result should we expect back?"

## Included tools

The v1 adapter evaluates this practical open-source stack:

- **FreeCAD** for CAD assembly, macros, drawings, and CalculiX-backed studies.
- **CadQuery** for reproducible Python-generated mechanical geometry.
- **cq_gears** when a candidate is gear-related, with a non-applicable result for belt/screw/direct-drive candidates.
- **OpenSCAD** for quick printable fixtures and simplified parametric prototypes.
- **BESO / FreeCAD Topology Optimization** for structural lightweighting after load cases are known.
- **CalculiX / Code_Aster** for FEA validation.
- **OpenMDAO** for multidisciplinary design optimization and Pareto sweeps.
- **ROS 2 + Gazebo / Ignition** for mechanism, controls, and factory-cell simulation.
- **Blender / Anton-style generative design** for optional mesh/digital-twin exploration.
- **Zoo Text-to-CAD / Text2CAD / DeepCAD research adapters** for optional experimental text-to-CAD concepts.

## How it works

`OpenSourceToolchainAdapterV1` is intentionally plan-only. It does not require heavyweight desktop CAD/FEA binaries inside the API container. Instead, it packages the normalized requirement, candidate components/performance, CAD artifact reference, simulation summary, and physics margins into per-tool `feed` payloads.

Each candidate response includes:

- `adapter_version` and `input_fingerprint` for traceability.
- `evaluated_tools` describing every supported tool.
- `tool_runs` with status, priority, feed payload, expected outputs, and artifact URI.
- `handoff_order` for runner orchestration.
- `result_contract` describing what an external runner should return.

## Disabling the adapter

For synchronous generation, set `toolchain_enabled` to `false` in the `/v1/candidates/generate` wrapper payload.

For worker jobs, set:

```bash
TOOLCHAIN_ADAPTER_ENABLED=false
```

When disabled, the pipeline appends `open-source toolchain adapter disabled` to response warnings and candidate `toolchain_results` is marked skipped.
