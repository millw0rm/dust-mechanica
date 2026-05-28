from packages.domain.schemas.requirements import RequirementInput
from packages.domain.services.pipeline import run_generation_pipeline
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


def test_toolchain_adapter_returns_all_supported_tool_contracts():
    candidate = {
        "id": "gear-demo",
        "topology": "gear-train-axis",
        "motor": {"id": "m1"},
        "drive": {"id": "d1"},
        "transmission": {"id": "planetary-10", "kind": "planetary_gear"},
        "achievable_speed": 1.2,
        "torque_margin": 0.4,
        "efficiency": 0.88,
        "total_mass": 4.2,
    }

    result = OpenSourceToolchainAdapterV1().run(normalized=_request(), candidate=candidate)

    evaluated_names = {tool["name"] for tool in result["evaluated_tools"]}
    run_names = {run["tool"] for run in result["tool_runs"]}
    assert evaluated_names <= run_names
    assert result["status"] == "planned"
    assert result["result_contract"]["execution_mode"] == "plan_only_until_external_runners_are_configured"
    assert next(run for run in result["tool_runs"] if run["tool"] == "cq_gears")["status"] == "ready_to_feed"


def test_pipeline_includes_toolchain_results_and_disable_warning():
    enabled = run_generation_pipeline(_request())
    assert enabled["candidates"]
    toolchain = enabled["candidates"][0]["toolchain_results"]
    assert toolchain["adapter_version"] == "toolchain-v1"
    assert "CadQuery" in toolchain["handoff_order"]

    disabled = run_generation_pipeline(_request(), toolchain_enabled=False)
    assert "open-source toolchain adapter disabled" in disabled["warnings"]
    assert disabled["candidates"][0]["toolchain_results"]["status"] == "skipped"
