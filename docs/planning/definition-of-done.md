# Definition of Done

A work item is considered **Done** only when all sections below are satisfied.

## 1) Functional Completion
- Acceptance criteria are implemented and demonstrably met.
- Edge cases and error paths for the story are handled.
- Feature flags/default behavior are explicitly defined (if applicable).

## 2) API Readiness Checks
- API contract (request/response fields, status codes, error shape) is documented and versioned.
- Backward-compatibility impact is assessed and recorded.
- Input validation and output guarantees are covered by tests.
- Idempotency, pagination, and rate-limit behavior are specified where relevant.

## 3) Documentation Checks
- User-facing and operator-facing docs are updated in the same change window.
- Any new configuration, environment variable, or runtime dependency is documented.
- Changelog/release notes entry is prepared when externally visible behavior changes.
- Architecture Decision Records (ADRs) are added/updated for non-trivial design choices.

## 4) Testing & Quality Checks
- Unit tests added/updated for all modified logic paths.
- Integration tests cover critical end-to-end behavior and failure modes.
- Regression tests are added for each fixed bug.
- CI pipeline passes on default quality gates (lint, type checks, tests, build).
- Performance-sensitive changes include benchmark evidence against baseline.

## 5) Traceability Checks
- Each commit references a task/work-item identifier.
- Pull request description maps requirements -> implementation -> tests.
- All major decisions and assumptions are captured in code comments or design docs.
- Logs/metrics/traces include identifiers needed to correlate request, solver run, and ranking output.

## 6) Security & Compliance Checks
- Threat surface review performed for new endpoints, inputs, and dependencies.
- Authentication/authorization checks verified for any access-controlled behavior.
- Secrets handling validated (no hard-coded secrets; secure storage/rotation paths documented).
- Dependency and container vulnerability scans completed with no unapproved high/critical findings.
- PII/data governance handling verified where relevant (collection, retention, redaction).

## 7) Operational Readiness
- Monitoring and alerting updated for new failure modes and SLO-impacting paths.
- Rollback/mitigation plan documented and tested for high-risk changes.
- Runbooks updated with diagnostic steps and ownership.
- On-call handoff notes prepared for releases with elevated risk.

## 8) Review & Approval Gates
- Code review approved by required reviewers.
- Product/domain sign-off obtained when ranking logic or catalog policy changes.
- QA/UAT sign-off captured for user-visible behavior changes.
- All blocking comments resolved (or explicitly accepted with rationale).
