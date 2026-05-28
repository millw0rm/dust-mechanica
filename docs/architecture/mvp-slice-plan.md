# MVP Slice Plan: Requirement → Topology Family → First-Pass Sizing → Ranking → Report

## Scope and Boundaries
This slice spans:
- `apps/api`: orchestration endpoint(s) + report artifact links.
- `packages/domain`: requirement profile schema, candidate family model, analytic check model, scoring model.
- `packages/engineering`: first-pass analytic sizing checks and margins.
- `packages/reporting`: JSON report builder + PDF placeholder emitter.

Single happy-path flow only. No optimizer loops, no CAD geometry generation, and no external solver dependency in this slice.

---

## 1) Constrained requirement profile
### MVP behavior
Accept exactly one constrained profile per request.

**Input fields (v1, required unless noted):**
- `motion_type`: enum (`linear`)
- `travel_mm`: number > 0
- `payload_kg`: number > 0
- `peak_speed_mm_s`: number > 0
- `peak_accel_mm_s2`: number > 0
- `duty_cycle_pct`: number (0,100]
- `orientation`: enum (`horizontal` | `vertical`)
- `positioning_repeatability_mm`: number > 0
- `supply_voltage_v`: enum (`24` | `48`)
- `environment`: enum (`clean_indoor`)
- `priority_weights`: object with `performance`, `cost`, `risk` where sum == 1.0

### API contract (proposed)
`POST /v1/slice/topology-evaluate`
- Request: one profile object.
- Response: one evaluated family with scored candidates and report links.

Validation is strict; any missing/out-of-range value returns `400` with field-level errors.

---

## 2) Generate one topology candidate family
### MVP behavior
Generate exactly one candidate family selected by a deterministic rule from the profile.

**Initial family supported:**
- `belt_driven_linear_axis`

**Family generation output includes:**
- family metadata (`id`, `name`, `assumptions`)
- 2–3 parameterized candidates (e.g., pulley diameter, belt width, motor frame proxy)
- candidate-level assumptions snapshot

### Deterministic selection rule (v1)
- If `motion_type=linear` and `peak_speed_mm_s >= 300`, choose belt-driven family.
- Otherwise still choose belt-driven family (temporary MVP fallback) but emit risk flag `family_selection_fallback=true`.

---

## 3) First-pass analytic sizing checks
### MVP behavior
For each generated candidate, run simple sanity checks and compute margins.

**Checks (v1):**
1. **Speed feasibility**: candidate max linear speed vs requirement peak speed.
2. **Force feasibility**: required force from payload + acceleration (+ orientation effect) vs candidate available linear force.
3. **Torque feasibility**: required motor torque via pulley radius vs candidate continuous/peak torque proxy.

**Outputs per check:**
- `required`
- `available`
- `margin_abs = available - required`
- `margin_pct = (available-required)/required`
- `status`: `pass` if margin_abs >= 0 else `fail`

**Candidate overall check status:**
- `pass` only if all three checks pass.
- If any fail, candidate stays in list with fail reasons (no silent filtering).

---

## 4) Rank candidates with weighted score
### MVP behavior
Compute a single weighted score per candidate and rank descending.

**Score dimensions (normalized 0..1):**
- `performance_score`: based on positive margins (speed/force/torque), clipped.
- `cost_score`: inverse relative cost index (heuristic table for candidate variants).
- `risk_score`: inverse risk penalty (assumption uncertainty + fallback flags).

**Final score:**
`total_score = w_perf*performance_score + w_cost*cost_score + w_risk*risk_score`
using `priority_weights` from request (validated to sum to 1.0).

**Tie-breakers:**
1. Higher `risk_score`
2. Higher minimum check margin_pct
3. Stable deterministic order by `candidate_id`

---

## 5) Return downloadable report JSON/PDF placeholder
### MVP behavior
Produce:
1. Full result payload in response.
2. Persisted JSON report artifact.
3. PDF placeholder artifact (stub content, clearly marked non-final).

**Artifact metadata in API response:**
- `report.json_url`
- `report.pdf_url`
- `report.generated_at_utc`
- `report.schema_version`

### Report contents
- Input requirement profile
- Generated family and candidates
- All analytic checks and margins
- Weighted scoring table + final ranking
- Assumptions list
- Risk flags list
- Trace IDs for reproducibility

**Risk flags examples:**
- `family_selection_fallback`
- `cost_model_heuristic`
- `torque_proxy_used`
- `no_thermal_duty_derating`

---

## Cross-package responsibilities
## `packages/domain`
- Define DTO/schema types:
  - `RequirementProfileV1`
  - `TopologyFamily`
  - `TopologyCandidate`
  - `SizingCheckResult`
  - `CandidateScore`
  - `EvaluationReport`
- Central validation rules and error enums.

## `packages/engineering`
- Implement deterministic family generator for belt-driven axis.
- Implement first-pass sizing calculators/check evaluators.
- Emit check-by-check margins + pass/fail.

## `packages/reporting`
- JSON report serializer + storage adapter interface.
- PDF placeholder renderer (template with summary/risk/assumptions).
- Artifact locator utility that returns downloadable URLs.

## `apps/api`
- Endpoint wiring + request validation + orchestration.
- Invoke domain/engineering/reporting modules in sequence.
- Return response contract including ranking and artifact links.

---

## Explicit acceptance criteria
1. **Single-profile ingestion**
   - Given a valid v1 profile, API returns `200` with one evaluated family and ≥2 candidates.
   - Given invalid profile fields, API returns `400` with machine-readable field errors.

2. **Family generation**
   - Family id is always `belt_driven_linear_axis` in MVP.
   - If profile does not meet preferred speed trigger, response includes `family_selection_fallback` risk flag.

3. **Analytic checks**
   - Every candidate includes speed/force/torque check results.
   - Each check includes required/available/margin_abs/margin_pct/status.
   - Candidate overall status reflects all-check pass/fail logic.

4. **Ranking**
   - Every candidate has `performance_score`, `cost_score`, `risk_score`, and `total_score`.
   - Ranking order is deterministic for identical inputs.

5. **Reporting artifacts**
   - Response includes non-empty `json_url` and `pdf_url`.
   - JSON artifact contains assumptions + risk flags + ranking table.
   - PDF artifact exists and contains clear placeholder marker.

6. **Traceability**
   - Response and persisted artifacts include shared trace/request id.

7. **Latency target (MVP non-functional)**
   - p95 response under 1.5s for single request in local dev profile.

---

## Demo script (end-to-end)
1. Start services for API and artifact storage adapter (local filesystem or mock object store).
2. Send sample request:
   - linear axis, 800 mm travel, 12 kg payload,
   - 600 mm/s peak speed, 2500 mm/s² accel,
   - horizontal orientation, 24V, clean indoor,
   - weights `{performance:0.5, cost:0.2, risk:0.3}`.
3. Verify response:
   - `family.id == belt_driven_linear_axis`
   - candidates present with check margins and pass/fail.
   - ranking includes weighted scores.
   - report artifact URLs present.
4. Download JSON report; verify assumptions and risk flags are present.
5. Download PDF placeholder; verify “placeholder / not for manufacturing release” marker.
6. Repeat with low-speed profile (e.g., 100 mm/s) and verify `family_selection_fallback` risk flag appears.

---

## Out of scope for this slice
- Multiple topology families or cross-family optimization.
- Motor catalog lookup or vendor pricing integration.
- Thermal life, resonance, deflection, and belt stretch detailed checks.
- CAD/FEA coupling.
- Production-grade PDF formatting.
