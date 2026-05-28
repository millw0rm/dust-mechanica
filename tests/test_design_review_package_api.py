import time
from fastapi.testclient import TestClient
from apps.api.main import app

client = TestClient(app)
PAYLOAD = {"requirement": {"topology":"belt-driven-linear-axis","functional_targets":{"travel":{"value":800,"unit":"mm"},"max_speed":{"value":1200,"unit":"mm/s"},"payload_mass":{"value":3,"unit":"kg"},"duty_cycle":0.7},"constraints":{"max_motor_power_w":400,"max_total_mass_kg":8}} ,"async_mode": True}


def test_design_review_package_requires_approval_and_returns_payload():
    jid = client.post('/v1/candidates/generate', json=PAYLOAD).json()["job_id"]
    for _ in range(50):
        s = client.get(f'/v1/jobs/{jid}').json()
        if s["status"] == "awaiting_review":
            break
        time.sleep(0.1)
    assert client.get(f'/v1/jobs/{jid}/design-review-package').status_code == 409
    client.post(f'/v1/jobs/{jid}/approve?note=ok&reason=qa')
    d = client.get(f'/v1/jobs/{jid}/design-review-package')
    assert d.status_code == 200
    assert "ranked_candidates" in d.json()
