import json

from packages.engineering.adapters.artifacts.local import LocalArtifactStore
from packages.domain.schemas.requirements import RequirementInput
from packages.engineering.adapters.toolchain.v1 import OpenSourceToolchainAdapterV1


def _request():
    return RequirementInput(
        functional_targets={
            "travel": {"value": 800, "unit": "mm"},
            "max_speed": {"value": 1200, "unit": "mm/s"},
            "payload_mass": {"value": 3, "unit": "kg"},
            "duty_cycle": 0.7,
        },
        constraints={"max_motor_power_w": 400, "max_total_mass_kg": 8},
    )


def test_local_artifact_store_uses_deterministic_toolchain_paths(tmp_path):
    store = LocalArtifactStore(tmp_path / "artifacts")
    payload = {"b": 2, "a": {"nested": True}}

    uri = store.put_json("toolchain", "abc123", "cadquery", "feed.json", payload)

    assert uri == "artifact://toolchain/abc123/cadquery/feed.json"
    assert store.path_for_uri(uri) == tmp_path / "artifacts" / "toolchain" / "abc123" / "cadquery" / "feed.json"
    assert json.loads(store.get(uri)) == payload


def test_toolchain_adapter_persists_json_artifacts_with_stable_uris(tmp_path):
    store = LocalArtifactStore(tmp_path / "artifacts")
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

    first = OpenSourceToolchainAdapterV1(artifact_store=store).run(normalized=_request(), candidate=candidate)
    second = OpenSourceToolchainAdapterV1(artifact_store=store).run(normalized=_request(), candidate=candidate)

    assert first["input_fingerprint"] == second["input_fingerprint"]
    first_cadquery = next(run for run in first["tool_runs"] if run["tool"] == "CadQuery")
    second_cadquery = next(run for run in second["tool_runs"] if run["tool"] == "CadQuery")
    assert first_cadquery["artifact_uris"] == second_cadquery["artifact_uris"]
    assert first_cadquery["artifact_uris"]["feed"].endswith("/cadquery/feed.json")
    assert json.loads(store.get(first_cadquery["artifact_uris"]["feed"])) == first_cadquery["feed"]
