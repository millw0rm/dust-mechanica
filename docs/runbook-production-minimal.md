# Minimal Production Runbook

## Environment Variables
- `API_ENV`
- `LOG_LEVEL`

## Deploy
1. Build API container from `Dockerfile.api`.
2. Build worker container from `Dockerfile.worker`.
3. Provide persistent volume for `/.data/jobs.db`.
