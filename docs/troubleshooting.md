# Troubleshooting
- Stuck queued jobs: ensure API startup spawned worker thread.
- Failed jobs: inspect `error` from `/v1/jobs/{id}` and structured logs containing trace and request IDs.
- Bad input: call `/v1/requirements/validate` first.
