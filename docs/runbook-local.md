# Local Runbook
Run API: `uvicorn apps.api.main:app --reload`.
Async usage: POST `/v1/candidates/generate?async_mode=true`, then poll GET `/v1/jobs/{id}`.
Storage: SQLite at `./.data/jobs.db`.
