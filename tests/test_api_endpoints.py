from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)
PAYLOAD = {"topology":"belt-driven-linear-axis","functional_targets":{"travel":{"value":800,"unit":"mm"},"max_speed":{"value":1200,"unit":"mm/s"},"payload_mass":{"value":3,"unit":"kg"},"duty_cycle":0.7},"constraints":{"max_motor_power_w":400,"max_total_mass_kg":8}}


def test_health():
    r = client.get('/health')
    assert r.status_code == 200


def test_validate_and_generate():
    r = client.post('/v1/requirements/validate', json=PAYLOAD)
    assert r.status_code == 200
    assert "normalized" in r.json()
    r2 = client.post('/v1/candidates/generate', json=PAYLOAD)
    assert r2.status_code == 200
    assert isinstance(r2.json()["candidates"], list)


def test_job_status():
    r = client.get('/v1/jobs/abc')
    assert r.status_code == 200
    assert r.json()["id"] == "abc"
