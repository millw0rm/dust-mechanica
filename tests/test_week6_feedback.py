from fastapi.testclient import TestClient
from apps.api.main import app
from packages.domain.repositories.jobs import JobRepository
from packages.domain.schemas.common import JobStatus
from datetime import datetime, timedelta, timezone


def test_feedback_and_telemetry_summary():
    c = TestClient(app)
    payload = {
        "requirement": {
            "request_id": "week6-feedback",
            "functional_targets": {
                "travel": {"value": 300, "unit": "mm"},
                "max_speed": {"value": 0.5, "unit": "m/s"},
                "payload_mass": {"value": 5.0, "unit": "kg"},
                "duty_cycle": 0.3,
            },
            "load_profile": {"horizontal_force": {"value": 80, "unit": "N"}},
            "environment": {"ambient_temp": {"value": 25, "unit": "degC"}},
            "constraints": {},
            "optimization_priorities": {
                "efficiency": 0.3,
                "cost": 0.3,
                "compactness": 0.2,
                "performance_margin": 0.2,
            },
        },
        "async_mode": True,
    }
    r = c.post("/v1/candidates/generate", json=payload)
    assert r.status_code == 200
    job_id = r.json()["job_id"]

    repo = JobRepository()
    repo.update(job_id, status=JobStatus.completed.value)

    fb = c.post(
        f"/v1/jobs/{job_id}/feedback",
        json={
            "rating": 4,
            "reviewer_id": "reviewer-1",
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "achieved_motion": True,
            "achieved_force": True,
            "achieved_pressure": False,
            "notes": "pilot observation",
        },
    )
    assert fb.status_code == 200

    summary = c.get("/v1/telemetry/summary")
    assert summary.status_code == 200
    data = summary.json()
    assert data["total_feedback"] >= 1
    assert "success_rates" in data


def test_feedback_duplicate_rejected():
    c = TestClient(app)
    repo = JobRepository()
    job_id = repo.create({}, {}, "", "feedback-dup")
    repo.update(job_id, status=JobStatus.completed.value)
    payload = {
        "rating": 5,
        "reviewer_id": "reviewer-dup",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "achieved_motion": True,
        "achieved_force": True,
        "achieved_pressure": True,
        "notes": "first",
    }
    assert c.post(f"/v1/jobs/{job_id}/feedback", json=payload).status_code == 200
    dup = c.post(f"/v1/jobs/{job_id}/feedback", json=payload)
    assert dup.status_code == 409


def test_feedback_invalid_status_rejected():
    c = TestClient(app)
    repo = JobRepository()
    job_id = repo.create({}, {}, "", "feedback-status")
    r = c.post(
        f"/v1/jobs/{job_id}/feedback",
        json={
            "rating": 3,
            "source_id": "anon-source",
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "achieved_motion": True,
            "achieved_force": False,
            "achieved_pressure": True,
            "notes": "queued should fail",
        },
    )
    assert r.status_code == 409


def test_feedback_window_expired_rejected():
    c = TestClient(app)
    repo = JobRepository()
    job_id = repo.create({}, {}, "", "feedback-expired")
    repo.update(job_id, status=JobStatus.completed.value)
    expired_time = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
    with repo._lock, repo._conn() as conn:
        conn.execute("update jobs set completed_at=? where id=?", (expired_time, job_id))

    r = c.post(
        f"/v1/jobs/{job_id}/feedback",
        json={
            "rating": 2,
            "source_id": "field-observer",
            "observed_at": datetime.now(timezone.utc).isoformat(),
            "achieved_motion": False,
            "achieved_force": False,
            "achieved_pressure": False,
            "notes": "too late",
        },
    )
    assert r.status_code == 409
