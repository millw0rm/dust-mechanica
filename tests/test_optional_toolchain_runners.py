from packages.engineering.adapters.artifacts.local import LocalArtifactStore
from packages.engineering.adapters.toolchain.executor import ToolchainExecutionService
from packages.engineering.adapters.toolchain.runners.calculix import (
    CalculixCodeAsterRunner,
)
from packages.engineering.adapters.toolchain.runners.freecad import FreeCADRunner
from packages.engineering.adapters.toolchain.runners.openmdao import OpenMDAORunner
from packages.engineering.adapters.toolchain.v1 import OpenSourceToolchainAdapterV1
from packages.domain.schemas.requirements import RequirementInput


def _toolchain_candidate():
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
    candidate["toolchain_results"] = OpenSourceToolchainAdapterV1().run(
        normalized=request, candidate=candidate
    )
    return candidate


def _tool_run(candidate, tool_name):
    return next(
        run
        for run in candidate["toolchain_results"]["tool_runs"]
        if run["tool"] == tool_name
    )


def test_optional_binary_runners_return_unavailable_when_binaries_are_missing(tmp_path):
    candidate = _toolchain_candidate()
    store = LocalArtifactStore(tmp_path / "artifacts")

    freecad = FreeCADRunner(
        store, executable_names=("definitely-missing-freecad",)
    ).run(_tool_run(candidate, "FreeCAD"))
    fea = CalculixCodeAsterRunner(
        store, executable_names=("definitely-missing-ccx",)
    ).run(_tool_run(candidate, "CalculiX / Code_Aster"))

    assert freecad["status"] == "unavailable"
    assert freecad["artifact_uris"] == {}
    assert freecad["availability"]["available"] is False
    assert fea["status"] == "unavailable"
    assert fea["artifact_uris"] == {}
    assert fea["availability"]["available"] is False


def test_openmdao_runner_returns_unavailable_when_module_is_missing(tmp_path):
    candidate = _toolchain_candidate()
    result = OpenMDAORunner(
        LocalArtifactStore(tmp_path / "artifacts"),
        module_name="definitely_missing_openmdao",
    ).run(_tool_run(candidate, "OpenMDAO"))

    assert result["status"] == "unavailable"
    assert result["artifact_uris"] == {}
    assert result["availability"]["available"] is False


def test_optional_runners_emit_artifacts_when_availability_checks_pass(
    tmp_path, monkeypatch
):
    candidate = _toolchain_candidate()
    store = LocalArtifactStore(tmp_path / "artifacts")
    monkeypatch.setattr(
        "packages.engineering.adapters.toolchain.runners.freecad.shutil.which",
        lambda _: "/usr/bin/fake",
    )
    monkeypatch.setattr(
        "packages.engineering.adapters.toolchain.runners.calculix.shutil.which",
        lambda _: "/usr/bin/fake",
    )
    monkeypatch.setattr(
        "packages.engineering.adapters.toolchain.runners.openmdao.importlib.util.find_spec",
        lambda _: object(),
    )

    cadquery_execution = ToolchainExecutionService(store).run_selected_tools(
        candidate=candidate, selected_tools=["CadQuery"]
    )["executions"][0]
    freecad_run = _tool_run(candidate, "FreeCAD")
    freecad_run = {
        **freecad_run,
        "feed": {
            **freecad_run["feed"],
            "upstream_artifact_uris": {"CadQuery": cadquery_execution["artifact_uris"]},
        },
    }
    freecad = FreeCADRunner(store).run(freecad_run)
    fea = CalculixCodeAsterRunner(store).run(
        _tool_run(candidate, "CalculiX / Code_Aster")
    )
    openmdao = OpenMDAORunner(store).run(_tool_run(candidate, "OpenMDAO"))

    assert freecad["status"] == "succeeded"
    assert freecad["artifact_uris"]["assembly_checks"].endswith(
        "/freecad/assembly-checks.json"
    )
    assert freecad["artifact_uris"]["drawing_handoff"].endswith(
        "/freecad/drawing-handoff.json"
    )
    assert (
        freecad["metadata"]["step_uri"] == cadquery_execution["artifact_uris"]["step"]
    )
    assert fea["status"] == "succeeded"
    assert fea["artifact_uris"]["margin_report"].endswith(
        "/calculix-code-aster/margin-report.json"
    )
    assert fea["metrics"]["status"] == "pass"
    assert openmdao["status"] == "succeeded"
    assert openmdao["artifact_uris"]["pareto_trace"].endswith(
        "/openmdao/pareto-trace.json"
    )
    assert openmdao["metrics"]["pareto_points"] >= 1


def test_execution_service_dispatches_optional_runners_with_upstream_artifacts(
    tmp_path, monkeypatch
):
    candidate = _toolchain_candidate()
    monkeypatch.setattr(
        "packages.engineering.adapters.toolchain.runners.freecad.shutil.which",
        lambda _: "/usr/bin/fake",
    )
    monkeypatch.setattr(
        "packages.engineering.adapters.toolchain.runners.calculix.shutil.which",
        lambda _: "/usr/bin/fake",
    )
    monkeypatch.setattr(
        "packages.engineering.adapters.toolchain.runners.openmdao.importlib.util.find_spec",
        lambda _: object(),
    )

    result = ToolchainExecutionService(
        LocalArtifactStore(tmp_path / "artifacts")
    ).run_selected_tools(
        candidate=candidate,
        selected_tools=["CadQuery", "FreeCAD", "CalculiX / Code_Aster", "OpenMDAO"],
    )

    assert result["status"] == "succeeded"
    assert [execution["status"] for execution in result["executions"]] == [
        "succeeded",
        "succeeded",
        "succeeded",
        "succeeded",
    ]
    assert result["artifact_uris"]["FreeCAD"]["drawing_handoff"].endswith(
        "/freecad/drawing-handoff.json"
    )
    assert result["executions"][2]["metrics"]["stress_margin"] >= 0
    assert result["executions"][3]["metrics"]["pareto_points"] >= 1


def test_execution_service_dispatches_optional_runners_as_unavailable(
    tmp_path, monkeypatch
):
    candidate = _toolchain_candidate()
    monkeypatch.setattr(
        "packages.engineering.adapters.toolchain.runners.freecad.shutil.which",
        lambda _: None,
    )
    monkeypatch.setattr(
        "packages.engineering.adapters.toolchain.runners.calculix.shutil.which",
        lambda _: None,
    )
    monkeypatch.setattr(
        "packages.engineering.adapters.toolchain.runners.openmdao.importlib.util.find_spec",
        lambda _: None,
    )

    result = ToolchainExecutionService(
        LocalArtifactStore(tmp_path / "artifacts")
    ).run_selected_tools(
        candidate=candidate,
        selected_tools=["FreeCAD", "CalculiX / Code_Aster", "OpenMDAO"],
    )

    assert result["status"] == "unavailable"
    assert [execution["status"] for execution in result["executions"]] == [
        "unavailable",
        "unavailable",
        "unavailable",
    ]
    assert result["artifact_uris"] == {}
