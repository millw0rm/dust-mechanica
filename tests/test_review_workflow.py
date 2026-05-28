import time
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)
PAYLOAD = {"topology":"belt-driven-linear-axis","functional_targets":{"travel":{"value":800,"unit":"mm"},"max_speed":{"value":1200,"unit":"mm/s"},"payload_mass":{"value":3,"unit":"kg"},"duty_cycle":0.7},"constraints":{"max_motor_power_w":400,"max_total_mass_kg":8}}


def _complete():
    r = client.post('/v1/candidates/generate?async_mode=true', json=PAYLOAD)
    jid = r.json()["job_id"]
    for _ in range(40):
        s = client.get(f'/v1/jobs/{jid}').json()
        if s["status"] == "awaiting_review":
            return jid
        time.sleep(0.1)
    raise AssertionError('not ready')


def test_approve_and_reject_transitions():
    jid = _complete()
    a = client.post(f'/v1/jobs/{jid}/approve?note=ok&reason=qa')
    assert a.status_code == 200
    assert a.json()["status"] == "approved"
