import time
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)
PAYLOAD = {"topology":"belt-driven-linear-axis","functional_targets":{"travel":{"value":800,"unit":"mm"},"max_speed":{"value":1200,"unit":"mm/s"},"payload_mass":{"value":3,"unit":"kg"},"duty_cycle":0.7},"constraints":{"max_motor_power_w":400,"max_total_mass_kg":8}}


def test_async_job_lifecycle_happy_path():
    r = client.post('/v1/candidates/generate?async_mode=true', json=PAYLOAD)
    assert r.status_code == 200
    job_id = r.json()["job_id"]
    for _ in range(30):
        s = client.get(f'/v1/jobs/{job_id}')
        assert s.status_code == 200
        if s.json()["status"] == "completed":
            assert s.json()["result"]["candidates"]
            return
        time.sleep(0.1)
    assert False, "job did not complete"
