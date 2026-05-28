# Risk Register

| ID | Risk | Type | Impact | Likelihood | Trigger / Early Warning | Mitigation | Owner |
|---|---|---|---|---|---|---|---|
| R-001 | **Unit inconsistency** across ingestion, solver constraints, and ranking inputs causes invalid comparisons or physically impossible outputs. | Technical + Domain | High | Medium | Increase in conversion-related validation failures; anomalous magnitude distributions; conflicting units in logs. | Enforce canonical unit schema, centralized conversion library, strict validators, and round-trip unit tests; block deploy on unit-check failures. | Data Engineering Lead |
| R-002 | **Solver nondeterminism** leads to unstable outputs across identical inputs, undermining trust and reproducibility. | Technical | High | Medium | Same-seed runs produce divergent decisions/scores; flaky CI in solver tests; unexplained objective variance. | Fixed-seed deterministic mode, variance harness in CI, decision-trace logging, and controlled randomization wrappers. | Optimization Lead |
| R-003 | **Catalog quality degradation** (missing fields, stale attributes, duplicate entities) reduces solution quality and ranking relevance. | Domain + Data | High | High | Rising ingestion reject rates, increased fallback usage, drops in ranking quality metrics on fresh data. | Data quality scorecards, schema contracts with providers, anomaly detection, and quarantine workflow for suspect records. | Catalog Manager |
| R-004 | **Overfitting ranking heuristics** to offline benchmark slices harms generalization in production traffic. | Technical + Product | High | Medium | Offline gains with online regression; outsized contribution from one heuristic; poor performance on long-tail segments. | Time-split validation, slice-based guardrails, heuristic ablation tests, online canary experiments, and rollback thresholds. | Ranking Lead |
| R-005 | Constraint model drift between documented business rules and implemented solver constraints introduces policy non-compliance. | Domain + Technical | High | Medium | Increased manual overrides; domain expert bug reports; mismatch between expected and produced recommendations. | Versioned rule catalog, traceable rule-to-constraint mapping, and scheduled domain review checkpoints. | Product + Optimization |
| R-006 | Performance regressions at scale (latency/memory) breach SLOs under realistic workload mix. | Technical | Medium-High | Medium | P95 solve latency trend upward; memory alarms; queue depth growth during peak periods. | Continuous performance benchmarks, resource budgets per change, and autoscaling plus graceful-degradation strategy. | Platform Lead |
| R-007 | Incomplete traceability impedes root-cause analysis for incorrect recommendations or solver failures. | Technical + Operations | Medium | Medium | Uncorrelated logs/traces; inability to reconstruct decision path for incident samples. | Mandatory trace IDs end-to-end, structured event schema, and observability completeness checks in CI/release gates. | SRE Lead |
| R-008 | Third-party dependency vulnerabilities expose system to exploitable risk. | Security | High | Medium | New CVEs affecting direct/transitive dependencies; failed security scans in CI. | Automated dependency scanning, patch SLAs by severity, and temporary compensating controls with documented expiry. | Security Engineer |

## Review Cadence
- Review and re-score risks at least once per sprint planning session.
- Revisit immediately after major incidents, architecture changes, or new data-provider onboarding.

## Scoring Notes
- Impact and likelihood are qualitative in this register; teams may map to numeric risk scores for portfolio tracking.
- Any risk rated High impact + Medium/High likelihood requires an explicit mitigation owner and due date in sprint planning.
