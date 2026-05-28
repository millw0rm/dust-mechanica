# How we ran this demo

## Commands

```bash
python - <<'PY'
from packages.domain.schemas.requirements import RequirementInput
from packages.domain.services.pipeline import run_generation_pipeline
# build request payload and run pipeline
PY
```

## Input profile
- Travel: 800 mm
- Max speed: 600 mm/s
- Payload: 12 kg
- Duty cycle: 0.7
- Constraint max motor power: 1200 W
- Constraint max total mass: 30 kg

## Output artifacts
- `request.json`: pipeline input payload
- `response.json`: full pipeline response
- `summary.json`: concise run summary
