# How we ran the comparative demo

## Command pattern

```bash
python - <<'PY'
from packages.domain.schemas.requirements import RequirementInput
from packages.domain.services.pipeline import run_generation_pipeline
# define two payloads, run both, write exports and comparison
PY
```

## Cases
- Case A baseline: 1200W max motor power, 30kg max mass
- Case B constrained: 500W max motor power, 6kg max mass

## Export set
- `case_a_baseline/request.json`
- `case_a_baseline/response.json`
- `case_a_baseline/summary.json`
- `case_b_constrained/request.json`
- `case_b_constrained/response.json`
- `case_b_constrained/summary.json`
- `COMPARE.json`
- `COMPARE.md`
