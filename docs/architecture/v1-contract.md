# V1 API Contract

## Purpose and Scope

This document defines the v1 contract for requirement ingestion, candidate generation, and asynchronous job status tracking. It standardizes request/response DTOs, units handling, lifecycle states, and error behavior for interoperable clients.

---

## 1) Requirement Payload Schema

`RequirementPayload` is the canonical input for synchronous validation and asynchronous design/candidate generation.

### 1.1 Top-level shape

```json
{
  "request_id": "string (uuid)",
  "functional_targets": { "...": "..." },
  "load_profile": { "...": "..." },
  "environment": { "...": "..." },
  "constraints": { "...": "..." },
  "controls": { "...": "..." },
  "optimization_priorities": { "...": "..." },
  "compliance": { "...": "..." },
  "metadata": { "...": "optional" }
}
```

### 1.2 Section definitions

#### A) `functional_targets`

Defines what the system must do.

- `target_flow_rate`: number/string quantity (e.g., `"1.5 m^3/s"`, `1500 "L/s"`)
- `target_head`: number/string quantity (e.g., `"42 m"`)
- `duty_cycle`: object with `mode` (`continuous|intermittent`) and `uptime_fraction` (0–1)
- `availability_target`: fraction (0–1)
- `response_time_limit_ms`: number

#### B) `load_profile`

Defines expected operating loads over time.

- `nominal`: operating point quantities
- `peak`: operating point quantities
- `transient_events`: array of `{ name, duration_s, recurrence_per_day, severity }`
- `profile_shape`: `steady|diurnal|batch|custom`

#### C) `environment`

Defines external and site conditions.

- `ambient_temperature`: quantity
- `fluid_temperature`: quantity
- `altitude`: quantity
- `humidity_rh`: fraction (0–1)
- `ingress_rating_required`: enum (`IP54`, `IP55`, `IP65`, etc.)
- `installation_location`: `indoor|outdoor|submerged`

#### D) `constraints`

Hard limits that candidate designs cannot violate.

- `max_footprint`: `{ length, width, height }` quantities
- `max_mass`: quantity
- `power_limits`: `{ max_input_power, supply_voltage, phases, frequency_hz }`
- `budget_cap`: currency amount with ISO 4217 code
- `preferred_vendors`: string array
- `excluded_materials`: string array

#### E) `controls`

Control/automation and integration requirements.

- `control_mode`: `open_loop|pid|model_predictive`
- `interfaces_required`: string array (e.g., `"Modbus TCP"`, `"CAN"`)
- `telemetry_fields`: string array
- `update_rate_hz`: number
- `fail_safe_state`: string

#### F) `optimization_priorities`

Relative weighting (0–1; sum SHOULD equal 1.0).

- `efficiency_weight`
- `capex_weight`
- `opex_weight`
- `maintainability_weight`
- `noise_weight`
- `mass_weight`

#### G) `compliance`

Regulatory and internal policy constraints.

- `required_standards`: array (e.g., `"ISO 12100"`, `"IEC 60204-1"`)
- `regional_requirements`: array (e.g., `"US-OSHA"`, `"EU-CE"`)
- `documentation_level`: `basic|full_traceable`
- `audit_retention_days`: integer

---

## 2) Standard Units Policy

### 2.1 Canonical storage

All dimensional values MUST be normalized to SI base/derived units before persistence or solver execution.

- Length: `m`
- Mass: `kg`
- Time: `s`
- Temperature: `K` (or `degC` converted to `K` internally)
- Pressure: `Pa`
- Flow rate: `m^3/s`
- Power: `W`
- Energy: `J`
- Frequency: `Hz`

Persisted DTO fields SHOULD include:

- `value_si` (numeric)
- `unit_si` (string)
- `source_value` (original scalar/string)
- `source_unit` (as submitted)

### 2.2 Input normalization rules

1. If numeric + explicit unit provided, parse and convert to SI.
2. If numeric without unit and field has default unit, apply field default and mark `assumed_unit=true`.
3. If string quantity provided (e.g., `"150 kPa"`), parse scalar and unit.
4. Temperatures in Celsius MUST be offset-converted (`K = degC + 273.15`).
5. Fractions MAY be provided as percent strings (e.g., `"97%"`) and are normalized to [0,1].
6. Currency fields are not converted to SI; they are stored as `{ amount, currency }`.

### 2.3 Unit parsing errors

Validation MUST reject ambiguous or invalid unit expressions with `422 Unprocessable Entity`.

Error codes:

- `UNIT_MISSING`: required unit absent and no default exists
- `UNIT_UNKNOWN`: unit token not recognized
- `UNIT_INCOMPATIBLE`: incompatible dimensions for field
- `UNIT_AMBIGUOUS`: expression can map to multiple dimensions
- `VALUE_OUT_OF_RANGE`: parsed quantity outside allowed bounds

---

## 3) Candidate Output Schema

`CandidateOutput` represents a ranked candidate returned by the optimizer.

### 3.1 Shape

```json
{
  "candidate_id": "string",
  "rank": 1,
  "topology": {
    "architecture": "string",
    "stages": [],
    "control_strategy": "string"
  },
  "selected_components": [
    {
      "role": "string",
      "part_number": "string",
      "vendor": "string",
      "qty": 1,
      "key_specs": {}
    }
  ],
  "performance_metrics": {
    "flow_rate_m3_s": 0.0,
    "head_m": 0.0,
    "input_power_w": 0.0,
    "efficiency": 0.0,
    "noise_db_a": 0.0
  },
  "margins": {
    "thermal_margin": 0.0,
    "power_margin": 0.0,
    "structural_margin": 0.0
  },
  "risks": [
    {
      "id": "string",
      "severity": "low|medium|high",
      "description": "string",
      "mitigation": "string"
    }
  ],
  "confidence": {
    "overall": 0.0,
    "data_quality": 0.0,
    "model_fit": 0.0
  }
}
```

### 3.2 Required sections

- `topology`: selected system architecture and major stage arrangement.
- `selected_components`: concrete part/vendor choices and quantities.
- `performance_metrics`: SI-normalized predicted operating metrics.
- `margins`: minimum safety/operability margins.
- `risks`: explicit uncertainty or integration risks.
- `confidence`: bounded [0,1] confidence signals.

---

## 4) Async Job Lifecycle

Long-running operations return a `job_id` and advance through standard states.

### 4.1 States

- `queued`: accepted, waiting for worker capacity.
- `running`: active execution in progress.
- `partial`: partial results available; further processing still ongoing.
- `failed`: terminal failure, no further retries unless explicitly resubmitted.
- `completed`: terminal success with final outputs.

### 4.2 Job status payload shape

```json
{
  "job_id": "string",
  "state": "queued|running|partial|failed|completed",
  "progress": 0.0,
  "created_at": "2026-05-28T12:00:00Z",
  "updated_at": "2026-05-28T12:00:10Z",
  "trace_id": "string",
  "partial_results": [],
  "result": null,
  "error": null,
  "links": {
    "self": "/v1/jobs/{job_id}",
    "cancel": "/v1/jobs/{job_id}/cancel"
  }
}
```

Rules:

- `progress` is a float from 0 to 1.
- `partial_results` MUST be non-empty when `state=partial`.
- `result` MUST be non-null only for `completed`.
- `error` MUST be non-null only for `failed`.

---

## 5) API Endpoint Contract Table

| Endpoint | Method | Request DTO | Success Response DTO | Error Response DTO | Notes |
|---|---|---|---|---|---|
| `/v1/requirements:validate` | `POST` | `RequirementPayload` | `ValidationResult` | `ValidationError` | Synchronous schema/unit validation only |
| `/v1/candidates:generate` | `POST` | `GenerateCandidatesRequest` (`requirement_payload`, `max_candidates`) | `AcceptedJob` (`job_id`, `state`) | `ValidationError` / `ServerError` | Async candidate generation; returns `202` |
| `/v1/jobs/{job_id}` | `GET` | path `job_id` | `JobStatus` | `NotFoundError` / `ServerError` | Poll job progress and retrieve outputs |
| `/v1/jobs/{job_id}/cancel` | `POST` | path `job_id` | `CancelResult` | `ConflictError` / `NotFoundError` | Best-effort cancellation |

### 5.1 Validation error format

All 4xx/5xx responses SHOULD include:

```json
{
  "error": {
    "code": "UNIT_INCOMPATIBLE",
    "message": "target_head requires pressure or length dimension",
    "field": "functional_targets.target_head",
    "details": {
      "received": "12 kg"
    }
  },
  "trace_id": "0f4b85d4f4a24d4b9e9872eb0ea1f67b"
}
```

### 5.2 Trace IDs

- Server MUST emit `trace_id` in every response payload and SHOULD mirror it in `X-Trace-Id` header.
- Clients SHOULD log and propagate trace IDs in support requests.

---

## Full JSON Examples

### A) Full request example (`RequirementPayload`)

```json
{
  "request_id": "c595d5ec-c0ad-4d0e-8f5a-72f9e30a6d0e",
  "functional_targets": {
    "target_flow_rate": "1.25 m^3/s",
    "target_head": "38 m",
    "duty_cycle": { "mode": "continuous", "uptime_fraction": 0.97 },
    "availability_target": 0.985,
    "response_time_limit_ms": 250
  },
  "load_profile": {
    "nominal": { "flow_rate": "1.0 m^3/s", "head": "34 m" },
    "peak": { "flow_rate": "1.4 m^3/s", "head": "42 m" },
    "transient_events": [
      { "name": "startup", "duration_s": 12, "recurrence_per_day": 4, "severity": "medium" }
    ],
    "profile_shape": "diurnal"
  },
  "environment": {
    "ambient_temperature": "35 degC",
    "fluid_temperature": "22 degC",
    "altitude": "850 m",
    "humidity_rh": "70%",
    "ingress_rating_required": "IP55",
    "installation_location": "outdoor"
  },
  "constraints": {
    "max_footprint": { "length": "2.2 m", "width": "1.6 m", "height": "1.8 m" },
    "max_mass": "1900 kg",
    "power_limits": {
      "max_input_power": "180 kW",
      "supply_voltage": "480 V",
      "phases": 3,
      "frequency_hz": 60
    },
    "budget_cap": { "amount": 420000, "currency": "USD" },
    "preferred_vendors": ["VendorA", "VendorB"],
    "excluded_materials": ["lead"]
  },
  "controls": {
    "control_mode": "pid",
    "interfaces_required": ["Modbus TCP", "4-20mA"],
    "telemetry_fields": ["flow_rate", "head", "motor_current", "bearing_temp"],
    "update_rate_hz": 5,
    "fail_safe_state": "safe_shutdown"
  },
  "optimization_priorities": {
    "efficiency_weight": 0.35,
    "capex_weight": 0.20,
    "opex_weight": 0.20,
    "maintainability_weight": 0.15,
    "noise_weight": 0.05,
    "mass_weight": 0.05
  },
  "compliance": {
    "required_standards": ["ISO 12100", "IEC 60204-1"],
    "regional_requirements": ["US-OSHA"],
    "documentation_level": "full_traceable",
    "audit_retention_days": 2555
  },
  "metadata": {
    "submitted_by": "ops-eng@example.com",
    "project_code": "DM-PUMP-042"
  }
}
```

### B) Full candidate output example (`CandidateOutput`)

```json
{
  "candidate_id": "cand_01J0XRXQXJQ6Q2TZJQ0Q9G6M1D",
  "rank": 1,
  "topology": {
    "architecture": "dual-stage centrifugal + VFD",
    "stages": [
      { "name": "stage_1", "type": "centrifugal", "head_m": 20.5 },
      { "name": "stage_2", "type": "centrifugal", "head_m": 19.0 }
    ],
    "control_strategy": "PID with flow feedback and pressure override"
  },
  "selected_components": [
    {
      "role": "primary_pump",
      "part_number": "PA-2200-60",
      "vendor": "VendorA",
      "qty": 2,
      "key_specs": { "rated_power_w": 75000, "rated_flow_m3_s": 0.72 }
    },
    {
      "role": "variable_frequency_drive",
      "part_number": "VFD-480-200A",
      "vendor": "VendorB",
      "qty": 2,
      "key_specs": { "max_current_a": 200, "efficiency": 0.985 }
    }
  ],
  "performance_metrics": {
    "flow_rate_m3_s": 1.28,
    "head_m": 39.3,
    "input_power_w": 152400,
    "efficiency": 0.842,
    "noise_db_a": 77.5
  },
  "margins": {
    "thermal_margin": 0.18,
    "power_margin": 0.12,
    "structural_margin": 0.25
  },
  "risks": [
    {
      "id": "risk_vendor_lead_time",
      "severity": "medium",
      "description": "VFD lead times exceed 10 weeks in current region.",
      "mitigation": "Approve alternate qualified VFD part numbers."
    }
  ],
  "confidence": {
    "overall": 0.86,
    "data_quality": 0.90,
    "model_fit": 0.83
  }
}
```

### C) Full job status example (`JobStatus`)

```json
{
  "job_id": "job_01J0XS4P4F3W3Y39F7MCT12R1A",
  "state": "partial",
  "progress": 0.62,
  "created_at": "2026-05-28T12:00:00Z",
  "updated_at": "2026-05-28T12:00:23Z",
  "trace_id": "6cb146245b3e46f188d8a07a1c6f0bf3",
  "partial_results": [
    {
      "candidate_id": "cand_01J0XRXQXJQ6Q2TZJQ0Q9G6M1D",
      "rank": 1,
      "score": 0.91
    }
  ],
  "result": null,
  "error": null,
  "links": {
    "self": "/v1/jobs/job_01J0XS4P4F3W3Y39F7MCT12R1A",
    "cancel": "/v1/jobs/job_01J0XS4P4F3W3Y39F7MCT12R1A/cancel"
  }
}
```
