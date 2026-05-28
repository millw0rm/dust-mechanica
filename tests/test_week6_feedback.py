from fastapi.testclient import TestClient
from apps.api.main import app


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

    fb = c.post(
        f"/v1/jobs/{job_id}/feedback",
        json={
            "rating": 4,
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
