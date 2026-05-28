from packages.engineering.adapters.cad.v1 import CADAdapterV1


def test_cad_artifact_contract():
    art = CADAdapterV1().build({"components": {"motor": "M1"}})
    assert art["artifact_id"].startswith("cad-")
    assert "component_manifest" in art
