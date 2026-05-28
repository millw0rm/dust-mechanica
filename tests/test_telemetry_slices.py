from datetime import datetime, timezone

from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routes import candidates
from packages.domain.repositories.jobs import JobRepository
from packages.domain.schemas.common import JobStatus


def _seed_job(repo: JobRepository, request_id: str, topology: str, policy_version: str):
    job_id = repo.create({}, {}, "", request_id)
    repo.update(
        job_id,
        status=JobStatus.completed.value,
        result={
            "schema_version": "2.0",
            "candidates": [{"topology": topology}],
            "issues": [],
            "missing": [],
            "conflicts": [],
            "assumptions": {},
            "policy_version": policy_version,
            "topology_selection_trace": {},
            "topology_candidate_stats": {},
        },
    )
    return job_id


def test_telemetry_slices_grouping(tmp_path):
    repo = JobRepository(path=str(tmp_path / "jobs.db"))
    candidates.repo = repo
    client = TestClient(app)

    j1 = _seed_job(repo, "s1", "belt", "v1")
    j2 = _seed_job(repo, "s2", "belt", "v1")
    j3 = _seed_job(repo, "s3", "screw", "v2")

    ts = datetime(2026, 5, 20, 12, 0, tzinfo=timezone.utc).isoformat()
    for job_id, rating in [(j1, 5), (j2, 3), (j3, 4)]:
        repo.add_feedback(job_id, {"reviewer_id": f"r-{job_id}", "observed_at": ts, "rating": rating, "achieved_motion": True, "achieved_force": True, "achieved_pressure": False, "notes": ""})

    res = client.get("/v1/telemetry/slices?bucket=daily")
    assert res.status_code == 200
    payload = res.json()
    assert payload["bucket"] == "daily"
    assert len(payload["slices"]) == 2

    belt = next(x for x in payload["slices"] if x["topology"] == "belt")
    assert belt["total_feedback"] == 2
    assert belt["avg_rating"] == 4.0
