import json

from packages.engineering.adapters.artifacts.local import LocalArtifactStore
from packages.engineering.adapters.toolchain.runners.cadquery import CadQueryRunner


def test_cadquery_runner_exports_placeholder_artifact_records(tmp_path):
    store = LocalArtifactStore(tmp_path / "artifacts")
    tool_run = {
        "tool": "CadQuery",
        "feed": {
            "input_fingerprint": "cadquerytest001",
            "topology": "belt-axis",
            "components": {"motor": "m1", "drive": "d1", "transmission": "belt-5m"},
            "performance": {"total_mass_kg": 4.2},
            "envelope": {"assumed_max_envelope_mm": [320, 80, 42]},
        },
    }

    result = CadQueryRunner(artifact_store=store).run(tool_run)

    assert result["status"] == "succeeded"
    assert result["runner_version"] == "cadquery-runner-v1"
    assert set(result["artifact_uris"]) >= {"step", "stl", "manifest"}
    assert result["artifact_uris"]["step"] == "artifact://toolchain/cadquerytest001/cadquery/placeholder.step"
    assert result["artifact_uris"]["stl"] == "artifact://toolchain/cadquerytest001/cadquery/placeholder.stl"
    assert result["metrics"] == {
        "component_count": 3,
        "component_pad_count": 3,
        "envelope_volume_mm3": 1075200.0,
        "envelope_surface_area_mm2": 84800.0,
        "step_bytes": 1456,
        "stl_bytes": 2584,
        "source_bytes": 855,
        "total_mass_kg": 4.2,
    }
    assert store.get(result["artifact_uris"]["step"]).startswith(b"ISO-10303-21")
    assert store.get(result["artifact_uris"]["stl"]).startswith(b"solid dust_mechanica_placeholder")
    manifest = json.loads(store.get(result["artifact_uris"]["manifest"]))
    assert manifest["envelope_mm"] == {"length": 320.0, "width": 80.0, "height": 42.0}
    assert manifest["components"]["motor"] == "m1"
    assert manifest["performance"] == {"total_mass_kg": 4.2}


def test_cadquery_runner_artifact_records_are_deterministic_for_sample_candidate(tmp_path):
    tool_run = {
        "tool": "CadQuery",
        "feed": {
            "input_fingerprint": "cadqueryrepeat01",
            "topology": "belt-axis",
            "components": {"motor": "m1", "drive": "d1", "transmission": "belt-5m"},
            "performance": {
                "achievable_speed_mps": 1.2,
                "torque_margin": 0.4,
                "efficiency": 0.88,
                "total_mass_kg": 4.2,
            },
            "envelope": {"assumed_max_envelope_mm": [320, 80, 42]},
        },
    }
    first_store = LocalArtifactStore(tmp_path / "first")
    second_store = LocalArtifactStore(tmp_path / "second")

    first = CadQueryRunner(artifact_store=first_store).run(tool_run)
    second = CadQueryRunner(artifact_store=second_store).run(tool_run)

    assert first["artifact_uris"] == second["artifact_uris"]
    assert first["metrics"] == second["metrics"]
    for artifact_uri in first["artifact_uris"].values():
        assert first_store.get(artifact_uri) == second_store.get(artifact_uri)


def test_cadquery_runner_accepts_adapter_cadquery_tool_run(tmp_path):
    from packages.domain.schemas.requirements import RequirementInput
    from packages.engineering.adapters.toolchain.v1 import OpenSourceToolchainAdapterV1

    request = RequirementInput(
        functional_targets={
            "travel": {"value": 800, "unit": "mm"},
            "max_speed": {"value": 1200, "unit": "mm/s"},
            "payload_mass": {"value": 3, "unit": "kg"},
            "duty_cycle": 0.7,
        },
        constraints={"max_motor_power_w": 400, "max_total_mass_kg": 8},
    )
    candidate = {
        "id": "belt-demo",
        "topology": "belt-axis",
        "motor": {"id": "m1"},
        "drive": {"id": "d1"},
        "transmission": {"id": "belt-5m", "kind": "belt"},
        "achievable_speed": 1.2,
        "torque_margin": 0.4,
        "efficiency": 0.88,
        "total_mass": 4.2,
    }
    plan = OpenSourceToolchainAdapterV1().run(normalized=request, candidate=candidate)
    tool_run = next(run for run in plan["tool_runs"] if run["tool"] == "CadQuery")

    result = CadQueryRunner(artifact_store=LocalArtifactStore(tmp_path / "artifacts")).run(tool_run)

    assert result["status"] == "succeeded"
    assert result["artifact_uris"]["step"].endswith("/cadquery/placeholder.step")
    assert result["artifact_uris"]["stl"].endswith("/cadquery/placeholder.stl")
    assert result["metrics"]["component_count"] == 3
    assert result["metrics"]["total_mass_kg"] == 4.2
    assert any("Missing envelope dimensions" in warning for warning in result["warnings"])
