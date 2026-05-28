# Week 6 Pilot Deployment + Feedback Loop

## Scope delivered
- User feedback capture endpoint: `POST /v1/jobs/{id}/feedback`
- Telemetry aggregate endpoint: `GET /v1/telemetry/summary`
- Stored feedback fields: rating, achieved motion/force/pressure, notes.

## Purpose
This enables pilot teams to report whether generated designs met desired outcomes in practical testing. The summary endpoint provides early calibration signals for model and rule tuning.

## Example
```bash
curl -X POST http://localhost:8000/v1/jobs/<id>/feedback \
  -H 'content-type: application/json' \
  -d '{"rating":4,"achieved_motion":true,"achieved_force":true,"achieved_pressure":false,"notes":"Pressure margin low at peak duty"}'
```

```bash
curl http://localhost:8000/v1/telemetry/summary
```
