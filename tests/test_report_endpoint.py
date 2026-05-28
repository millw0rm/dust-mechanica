import time
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)
PAYLOAD = {"topology":"belt-driven-linear-axis","functional_targets":{"travel":{"value":800,"unit":"mm"},"max_speed":{"value":1200,"unit":"mm/s"},"payload_mass":{"value":3,"unit":"kg"},"duty_cycle":0.7},"constraints":{"max_motor_power_w":400,"max_total_mass_kg":8}}


def test_report_endpoint_contract():
    r = client.post('/v1/candidates/generate?async_mode=true', json=PAYLOAD)
    jid = r.json()["job_id"]
    for _ in range(40):
        rr = client.get(f'/v1/jobs/{jid}/report')
        if rr.json().get("report"):
            assert "winner" in rr.json()["report"]
            return
        time.sleep(0.1)
    raise AssertionError('report missing')
