from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routes.candidates import repo
from packages.domain.schemas.common import JobStatus
from packages.domain.schemas.requirements import RequirementInput
from packages.domain.services.pipeline import run_generation_pipeline
from packages.reporting.explain import build_explainability_report

client = TestClient(app)


def _request() -> RequirementInput:
    return RequirementInput(
        topology="belt-driven-linear-axis",
        functional_targets={
            "travel": {"value": 800, "unit": "mm"},
            "max_speed": {"value": 1200, "unit": "mm/s"},
            "payload_mass": {"value": 3, "unit": "kg"},
            "duty_cycle": 0.7,
        },
        constraints={"max_motor_power_w": 400, "max_total_mass_kg": 8},
    )


def _completed_job() -> tuple[str, dict]:
    req = _request()
    result = run_generation_pipeline(req)
    job_id = repo.create(req.model_dump(), {"issues": [], "missing": [], "conflicts": []}, "trace-test", "")
    repo.update(
        job_id,
        status=JobStatus.awaiting_review.value,
        progress=1.0,
        result=result,
        report=build_explainability_report(result),
    )
    return job_id, result


def test_toolchain_run_endpoint_executes_cadquery_and_persists_artifacts():
    job_id, result = _completed_job()
    candidate_id = result["candidates"][0]["id"]

    response = client.post(
        f"/v1/jobs/{job_id}/toolchain/run",
        json={"candidate_id": candidate_id, "selected_tools": ["CadQuery"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "succeeded"
    assert body["executions"][0]["status"] == "succeeded"
    assert body["artifact_uris"]["CadQuery"]["step"].startswith("artifact://toolchain/")

    saved = client.get(f"/v1/jobs/{job_id}").json()
    saved_candidate = next(item for item in saved["result"]["candidates"] if item["id"] == candidate_id)
    assert saved_candidate["toolchain_results"]["latest_execution"]["artifact_uris"]["CadQuery"]["stl"].endswith("/cadquery/placeholder.stl")
    assert saved["report"]["toolchain_runs"][-1]["candidate_id"] == candidate_id


def test_toolchain_run_endpoint_marks_unsupported_tools_planned_only():
    job_id, result = _completed_job()
    candidate_id = result["candidates"][0]["id"]

    response = client.post(
        f"/v1/jobs/{job_id}/toolchain/run",
        json={"candidate_id": candidate_id, "selected_tools": ["FreeCAD", "NotARealTool"]},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "planned_only"
    assert [execution["status"] for execution in body["executions"]] == ["planned_only", "planned_only"]
    assert body["artifact_uris"] == {}
