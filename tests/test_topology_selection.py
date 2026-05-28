from packages.catalog.loader import load_catalog
from packages.domain.schemas.requirements import RequirementInput
from packages.domain.services.topology_selector import select_topologies
from packages.domain.services.pipeline import run_generation_pipeline


def _req():
    return RequirementInput.model_validate({
        "functional_targets": {
            "travel": {"value": 1.0, "unit": "m"},
            "max_speed": {"value": 0.5, "unit": "m/s"},
            "payload_mass": {"value": 3.0, "unit": "kg"},
            "duty_cycle": 0.6,
        },
        "constraints": {"max_motor_power_w": 3000, "max_total_mass_kg": 200},
        "priorities": {"efficiency": 0.25, "cost": 0.25, "compactness": 0.25, "performance_margin": 0.25},
    })


def test_topology_selector_returns_trace():
    req = _req()
    c = load_catalog()
    selection = select_topologies(req, c)
    assert "selected" in selection and selection["selected"]


def test_pipeline_respects_allowed_topologies():
    req = _req()
    result = run_generation_pipeline(req, allowed_topologies=["ball-screw-linear-axis"], explain_topology_selection=True)
    assert result["topology_selection_trace"]["selected"] == ["ball-screw-linear-axis"]
