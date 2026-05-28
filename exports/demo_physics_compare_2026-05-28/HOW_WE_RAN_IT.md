# How we ran the comparative demo

## Exact command

```bash
python scripts/export_physics_compare.py --output-dir exports/demo_physics_compare_2026-05-28
```

## Inputs

### Case A baseline

```json
{
  "functional_targets": {
    "travel": {
      "value": 800,
      "unit": "mm"
    },
    "max_speed": {
      "value": 600,
      "unit": "mm/s"
    },
    "payload_mass": {
      "value": 12,
      "unit": "kg"
    },
    "duty_cycle": 0.7
  },
  "constraints": {
    "max_motor_power_w": 1200,
    "max_total_mass_kg": 30
  }
}
```

### Case B constrained

```json
{
  "functional_targets": {
    "travel": {
      "value": 800,
      "unit": "mm"
    },
    "max_speed": {
      "value": 600,
      "unit": "mm/s"
    },
    "payload_mass": {
      "value": 12,
      "unit": "kg"
    },
    "duty_cycle": 0.7
  },
  "constraints": {
    "max_motor_power_w": 500,
    "max_total_mass_kg": 6
  }
}
```

## Execution details

- The script constructs `RequirementInput` objects from the payloads above.
- Each case is run through `run_generation_pipeline(..., explain_topology_selection=True, sim_enabled=True, cad_enabled=False)`.
- CAD generation is disabled so the export is reproducible and does not include run-specific CAD artifact UUIDs.
- Physics enrichment comes from `physics_summary`, `physics_passed`, `physics_margins`, and `physics_warnings` on each candidate response.

## Export set

- `case_a_baseline/request.json`
- `case_a_baseline/response.json`
- `case_a_baseline/summary.json`
- `case_b_constrained/request.json`
- `case_b_constrained/response.json`
- `case_b_constrained/summary.json`
- `COMPARE.json`
- `COMPARE.md`
- `PHYSICS_COMPARE.json`
- `PHYSICS_COMPARE.md`
- `HOW_WE_RAN_IT.md`
