# Catalog Data Model

This document defines the catalog-facing data model for component selection and scoring in Dust Mechanica. It focuses on entities, compatibility/derating rules, temporal versioning, provenance, and reproducibility guarantees.

## 1) Core entities

The catalog is normalized around six core component entities. Each entity has a stable identifier (`id`), a human-visible key (`code` or `part_number`), lifecycle metadata, and provenance/versioning fields (defined later).

### Motor
- Purpose: Converts electrical energy to mechanical rotation/torque.
- Suggested fields:
  - `id`, `part_number`, `manufacturer`
  - `motor_type` (e.g., BLDC, stepper, brushed DC)
  - `rated_voltage_v`, `kv_rating`, `rated_torque_nm`, `peak_torque_nm`
  - `rated_speed_rpm`, `max_speed_rpm`, `rated_current_a`, `peak_current_a`
  - `shaft_diameter_mm`, `mass_g`, `thermal_resistance_c_per_w`

### Drive
- Purpose: Power/control electronics that operate motors.
- Suggested fields:
  - `id`, `part_number`, `manufacturer`
  - `supported_motor_types[]`
  - `input_voltage_min_v`, `input_voltage_max_v`
  - `continuous_current_a`, `peak_current_a`
  - `control_interfaces[]` (PWM, CAN, UART, etc.)
  - `switching_frequency_hz`, `cooling_requirement`

### Transmission
- Purpose: Couples motor output to load with desired ratio/efficiency.
- Suggested fields:
  - `id`, `part_number`, `manufacturer`
  - `transmission_type` (gearbox, belt, chain, harmonic)
  - `ratio_min`, `ratio_max` (or fixed `ratio`)
  - `max_input_speed_rpm`, `continuous_torque_nm`, `peak_torque_nm`
  - `efficiency_nominal`, `backlash_deg`, `mount_pattern`

### Bearing
- Purpose: Supports rotating/moving elements with rated load/life.
- Suggested fields:
  - `id`, `part_number`, `manufacturer`
  - `bearing_type` (ball, roller, sleeve)
  - `bore_mm`, `outer_diameter_mm`, `width_mm`
  - `dynamic_load_rating_n`, `static_load_rating_n`
  - `max_speed_rpm`, `lubrication_type`, `sealed`

### Sensor
- Purpose: Measures position, speed, force, temperature, etc.
- Suggested fields:
  - `id`, `part_number`, `manufacturer`
  - `sensor_type` (encoder, hall, thermistor, IMU, load cell)
  - `measurement_min`, `measurement_max`, `resolution`, `accuracy`
  - `update_rate_hz`, `interface` (I2C/SPI/CAN/analog)
  - `supply_voltage_min_v`, `supply_voltage_max_v`

### Material
- Purpose: Engineering material records used for structural/thermal decisions.
- Suggested fields:
  - `id`, `material_grade`, `standard_spec`
  - `density_kg_m3`, `yield_strength_mpa`, `ultimate_strength_mpa`
  - `youngs_modulus_gpa`, `thermal_conductivity_w_mk`
  - `max_service_temp_c`, `corrosion_class`, `process_compatibility[]`

## 2) Compatibility and derating rule representation

Represent rules as explicit catalog objects rather than hard-coded logic.

## Rule object shape
- `rule_id`: stable UUID.
- `rule_type`: `compatibility` | `derating`.
- `applies_to`: entity pair or tuple (e.g., `motor-drive`, `motor-transmission-bearing`).
- `scope_filter`: predicate over attributes (JSONPath/CEL-like expression).
- `condition`: boolean expression for pass/fail or trigger threshold.
- `effect`:
  - Compatibility rule: `allow`/`deny` plus optional `reason_code`.
  - Derating rule: transforms limits using formula/table (e.g., `max_torque *= 0.82`).
- `severity`: `error` | `warning` (for soft constraints).
- `priority`: deterministic conflict resolution order.
- `effective_start`, `effective_end`: temporal applicability window.
- `version`: monotonically increasing integer or semver.

## Recommended evaluation semantics
1. Build candidate assembly.
2. Resolve active rules by `effective_*` and status.
3. Evaluate compatibility rules first; hard denies reject candidate.
4. Apply derating rules in priority order to produce adjusted limits.
5. Persist which rules fired and resulting adjusted values for auditability.

## 3) Versioning strategy (effective dates, superseded records)

Use **bi-temporal-lite** catalog versioning:

- Business validity:
  - `effective_start` (inclusive)
  - `effective_end` (exclusive, nullable for open-ended)
- Record lineage:
  - `record_version` (integer)
  - `supersedes_record_id` (nullable FK to prior version)
  - `is_superseded` (derived or materialized)

### Invariants
- No overlapping effective windows for the same logical item key (`part_number` or `material_grade`) unless explicitly allowed by region/manufacturer partition.
- New revisions create new rows; do not mutate prior effective history except to close `effective_end`.
- A superseding row must point to the immediate predecessor with `supersedes_record_id`.

### Querying
- “As-designed on date D”: select rows where `effective_start <= D < coalesce(effective_end, +∞)`.
- “Latest published”: max `record_version` among currently active rows.

## 4) Provenance fields (source, confidence, validation status)

Each entity row and rule row should carry provenance metadata:

- `source_system`: origin system/tool (PLM, vendor PDF ingestion, manual entry).
- `source_reference`: URL/file hash/document id/page locator.
- `source_retrieved_at`: timestamp of extraction.
- `ingested_by`: pipeline/user identifier.
- `confidence_score`: numeric `[0.0, 1.0]` confidence from extraction/normalization.
- `validation_status`: `unreviewed` | `auto_validated` | `human_validated` | `rejected`.
- `validated_by`, `validated_at`, `validation_notes`.
- `provenance_version`: schema version of provenance payload.

### Governance recommendations
- Reject promotion to production catalog if `validation_status = rejected`.
- Require `human_validated` for safety-critical parameters (torque/current/temperature/load ratings).
- Keep immutable raw-source snapshots keyed by `source_reference` hash.

## 5) Reproducibility rule

Every candidate result (ranking, feasibility check, optimization run) **must** persist a reproducibility envelope that references the exact catalog and rules versions used.

### Required result metadata
- `catalog_snapshot_id` or `{entity_type -> record_version set}`.
- `rule_snapshot_id` or `{rule_id -> version}`.
- `evaluation_timestamp`.
- `engine_version` (selection/scoring algorithm build).
- `input_fingerprint` (hash of normalized user requirements).

A result is non-compliant if these references are missing. Re-scoring or audit replay must load the recorded snapshots/versions, not current live tables.

## Migration strategy for schema changes

Adopt additive-first, backward-compatible migrations with explicit schema versioning.

### Principles
1. **Expand, migrate, contract**:
   - Expand: add new nullable columns/tables/fields.
   - Migrate: backfill + dual-write from application.
   - Contract: remove deprecated fields only after full cutover.
2. **Version every structural contract**:
   - `schema_version` at dataset/catalog level.
   - Versioned rule/provenance payloads (`rule_payload_version`, `provenance_version`).
3. **Deterministic transforms**:
   - Store migration scripts and checksums.
   - Ensure migrations are idempotent and reversible where feasible.
4. **Historical integrity**:
   - Never rewrite historical business-effective records for convenience.
   - If semantics change, create translated successor records and link lineage.

### Operational workflow
1. Author migration RFC documenting field mapping, defaults, and rollback.
2. Ship DDL (expand phase) behind feature flags.
3. Run backfill jobs; validate row counts, null rates, and rule replay parity.
4. Enable dual-read/dual-write, compare outputs, then cut over reads.
5. Freeze writes to deprecated fields, then contract in later release.

### Compatibility guarantees
- Minor schema upgrades must preserve ability to replay historical candidate evaluations.
- Breaking changes require a major `schema_version` bump and a compatibility adapter for at least one deprecation window.
