from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient

from apps.api.main import app
from apps.api.routes import candidates
from packages.domain.repositories.jobs import JobRepository
from packages.domain.schemas.common import JobStatus


def _job(repo: JobRepository, request_id: str):
    job_id = repo.create({}, {}, "", request_id)
    repo.update(job_id, status=JobStatus.completed.value, result={"schema_version": "2.0", "candidates": [{"topology": "belt"}], "issues": [], "missing": [], "conflicts": [], "assumptions": {}, "policy_version": "v1", "topology_selection_trace": {}, "topology_candidate_stats": {}})
    return job_id


def test_telemetry_drift_window_comparison(tmp_path):
    repo = JobRepository(path=str(tmp_path / "jobs.db"))
    candidates.repo = repo
    client = TestClient(app)

    now = datetime.now(timezone.utc)
    recent_job = _job(repo, "recent")
    baseline_job = _job(repo, "baseline")

    repo.add_feedback(recent_job, {"reviewer_id": "recent", "observed_at": (now - timedelta(days=2)).isoformat(), "rating": 5, "achieved_motion": True, "achieved_force": True, "achieved_pressure": True, "notes": ""})
    repo.add_feedback(baseline_job, {"reviewer_id": "baseline", "observed_at": (now - timedelta(days=10)).isoformat(), "rating": 2, "achieved_motion": False, "achieved_force": False, "achieved_pressure": False, "notes": ""})

    res = client.get("/v1/telemetry/drift?recent_days=7&baseline_days=14")
    assert res.status_code == 200
    data = res.json()
    assert data["sample_sizes"] == {"baseline": 1, "recent": 1}
    rating = next(m for m in data["metrics"] if m["metric"] == "rating")
    assert rating["baseline"] == 2.0
    assert rating["recent"] == 5.0
    assert rating["delta"] == 3.0
