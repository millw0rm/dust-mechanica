# Units and Uncertainty Design Rules

## Purpose
This document defines mandatory design rules for unit handling, conversion traceability, and uncertainty annotations so engineering calculations remain auditable and comparable across services.

## Rule 1: Every Numeric Field Carries Unit Metadata at Boundaries
All numeric values crossing system boundaries (API requests, job payloads, persistence DTOs, adapter contracts, and report exports) MUST include explicit unit metadata.

### Requirements
- Boundary fields MUST be represented as structured quantities, not naked scalars.
- Each quantity MUST preserve both original source representation and normalized representation.
- Dimensionless values MUST still be explicit about dimension semantics (e.g., fraction, ratio, percent).

### Recommended boundary shape
```json
{
  "value": 850,
  "unit": "N*m",
  "dimension": "torque",
  "source": {
    "value": "627 lbf*ft",
    "unit": "lbf*ft"
  }
}
```

## Rule 2: Internal Canonical Units Are Mandatory (SI Base/Derived)
All internal computation and persistence paths MUST use SI base/derived units as canonical values.

### Requirements
- Conversion to SI MUST happen immediately after parsing boundary input.
- Solvers, optimizers, and validators MUST consume only canonical SI values.
- Any non-SI representation is display-only and MUST be derived from canonical values.

### Canonical examples
- Torque: `N*m`
- Inertia (mass moment): `kg*m^2`
- Duty cycle: unitless fraction in `[0, 1]`
- Thermal limits:
  - Temperature: `K`
  - Temperature rise: `K`
  - Heat flux (if present): `W/m^2`

## Rule 3: Conversions Are Logged for Traceability
Every unit conversion MUST emit traceable audit metadata so downstream outputs can explain how final numbers were produced.

### Requirements
- Log each conversion event with input value/unit, output value/unit, converter version, and timestamp.
- Attach correlation identifiers (`request_id`, `trace_id`, `field_path`).
- Persist enough precision to reproduce downstream calculations within tolerance.

### Example conversion log entry
```json
{
  "request_id": "b13112d6-9805-4432-b3c6-0783906f2b80",
  "trace_id": "trc_01JY...",
  "field_path": "constraints.max_torque",
  "source_value": 627,
  "source_unit": "lbf*ft",
  "canonical_value": 850.11,
  "canonical_unit": "N*m",
  "converter_version": "units-lib@2.4.1",
  "timestamp_utc": "2026-05-28T12:15:09Z"
}
```

## Rule 4: Computed Outputs Include Margin, Sensitivity, and Confidence Annotations
All computed engineering outputs MUST include uncertainty context so users can assess robustness instead of relying on point estimates.

### Requirements
- **Margin**: distance to limiting constraint in canonical units and relative percentage.
- **Sensitivity**: first-order response to perturbations in key assumptions.
- **Confidence**: bounded score `[0,1]` with provenance (data quality + model fidelity).

### Required annotation shape
```json
{
  "output": {
    "value": 742.0,
    "unit": "N*m",
    "dimension": "torque"
  },
  "margin": {
    "absolute": 108.0,
    "unit": "N*m",
    "relative": 0.127
  },
  "sensitivity": [
    { "input": "fluid_temperature", "delta_input": 1.0, "input_unit": "K", "delta_output": -3.8, "output_unit": "N*m" },
    { "input": "supply_voltage", "delta_input": 1.0, "input_unit": "V", "delta_output": 2.1, "output_unit": "N*m" }
  ],
  "confidence": {
    "overall": 0.86,
    "data_quality": 0.88,
    "model_fit": 0.83
  }
}
```

## Rule 5: Validation Rejects Ambiguous Units and Impossible Ranges
Validation MUST fail fast on unclear dimensional intent or physically impossible values.

### Requirements
- Reject ambiguous expressions (`UNIT_AMBIGUOUS`) and unknown tokens (`UNIT_UNKNOWN`).
- Reject incompatible dimensions (`UNIT_INCOMPATIBLE`) for a field.
- Reject impossible or policy-forbidden ranges (`VALUE_OUT_OF_RANGE`).

### Baseline validation examples
- Negative absolute temperature in Kelvin is invalid.
- Duty cycle outside `[0, 1]` after normalization is invalid.
- Negative inertia is invalid.
- Thermal limit where warning threshold exceeds hard shutdown threshold is invalid.

## Domain Examples

### 1) Torque
**Accepted input**
```json
{ "value": "627 lbf*ft" }
```
**Canonical internal representation**
```json
{ "value_si": 850.11, "unit_si": "N*m", "dimension": "torque" }
```
**Rejected input example**
```json
{ "value": 850, "unit": "N" }
```
Reason: `UNIT_INCOMPATIBLE` (force is not torque).

### 2) Inertia (mass moment)
**Accepted input**
```json
{ "value": 12.5, "unit": "kg*m^2" }
```
**Canonical internal representation**
```json
{ "value_si": 12.5, "unit_si": "kg*m^2", "dimension": "mass_moment_of_inertia" }
```
**Rejected input example**
```json
{ "value": -0.2, "unit": "kg*m^2" }
```
Reason: `VALUE_OUT_OF_RANGE` (inertia cannot be negative).

### 3) Duty cycle
**Accepted inputs**
```json
{ "value": "97%" }
{ "value": 0.97, "unit": "fraction" }
```
**Canonical internal representation**
```json
{ "value_si": 0.97, "unit_si": "1", "dimension": "duty_cycle_fraction" }
```
**Rejected input example**
```json
{ "value": 1.2, "unit": "fraction" }
```
Reason: `VALUE_OUT_OF_RANGE` (must be in `[0,1]`).

### 4) Thermal limits
**Accepted input**
```json
{
  "max_winding_temp": { "value": 155, "unit": "degC" },
  "ambient_temp": { "value": 40, "unit": "degC" }
}
```
**Canonical internal representation**
```json
{
  "max_winding_temp": { "value_si": 428.15, "unit_si": "K" },
  "ambient_temp": { "value_si": 313.15, "unit_si": "K" },
  "temperature_margin": { "value_si": 115.0, "unit_si": "K" }
}
```
**Rejected input examples**
```json
{ "max_winding_temp": { "value": -5, "unit": "K" } }
{ "warning_temp": { "value": 180, "unit": "degC" }, "shutdown_temp": { "value": 160, "unit": "degC" } }
```
Reasons: `VALUE_OUT_OF_RANGE` (negative Kelvin) and invalid threshold ordering.
