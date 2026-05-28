# Milestones

## Sprint 1 — Foundations & Data Integrity

### Goals
- Establish a reliable baseline for ingesting and validating dust-mechanica catalog and input datasets.
- Define canonical units and conversion policies across all core entities.
- Stand up a deterministic baseline solver run mode for reproducible development and QA.

### Acceptance Criteria (Measurable)
1. **Schema and ingestion coverage**
   - 100% of required catalog fields are represented in versioned schemas.
   - Ingestion pipeline rejects malformed records with structured errors.
   - At least 95% of historical sample records pass validation on first run.
2. **Unit consistency guardrails**
   - All quantity-bearing fields are mapped to canonical units with explicit conversion tables.
   - 100% of conversion functions have unit tests, including boundary and round-trip checks.
   - Zero known silent unit coercions remain in the code path.
3. **Deterministic baseline run**
   - A fixed-seed solver mode produces byte-for-byte identical outputs across 20 repeated local runs.
   - CI executes deterministic mode and fails on output drift.

---

## Sprint 2 — Solver Reliability & Performance

### Goals
- Improve solver stability, constraint handling, and runtime predictability.
- Introduce nondeterminism detection and controlled randomness handling.
- Establish performance SLOs for representative workloads.

### Acceptance Criteria (Measurable)
1. **Reliability**
   - Solver success rate is >= 99% on the agreed benchmark suite.
   - Constraint violations in final solutions are 0 for hard constraints.
   - Retry/fallback paths are exercised by tests with >= 90% branch coverage in solver orchestration modules.
2. **Nondeterminism control**
   - Differential run harness reports variance metrics across 50 repeated runs.
   - P95 objective-score variance is below agreed threshold (e.g., < 0.5%).
   - Any nondeterministic branch is logged with seed and decision trace.
3. **Performance**
   - P95 end-to-end solve time meets sprint SLO (e.g., <= 2s on reference hardware/workload).
   - Memory footprint remains below defined cap (e.g., <= 1.5 GB RSS at P95).

---

## Sprint 3 — Ranking Quality, Explainability & Readiness

### Goals
- Validate ranking quality against offline truth sets and guard against heuristic overfitting.
- Improve traceability and decision explainability.
- Prepare release-readiness gates across API, docs, security, and operations.

### Acceptance Criteria (Measurable)
1. **Ranking quality**
   - Offline evaluation improves agreed core metrics (e.g., NDCG@K / precision@K) by target delta vs baseline.
   - No regression > 1% in protected or critical scenario slices.
   - Heuristic contributions are ablated and documented; no single heuristic dominates > configured cap without approval.
2. **Explainability & traceability**
   - 100% of production ranking responses include trace IDs and feature contribution summaries.
   - Decision trails can be reconstructed for at least 99% of sampled requests.
3. **Release readiness**
   - Definition-of-done checklist passes for all in-scope stories.
   - Security review findings at severity high/critical are 0 open before release tag.

---

## Cross-Sprint Operating Metrics

- Story completion predictability: planned vs completed points variance <= 20% per sprint.
- Escaped defect rate: <= 2 medium+ defects per sprint attributable to in-scope changes.
- Test suite health: CI pass rate >= 95% on default branch and mean time to restore < 4 hours.
