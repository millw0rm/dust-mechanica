# Module Boundaries

## Purpose
This document defines module boundaries for the planned repository layout so teams can scale work safely without introducing hidden cross-layer coupling.

## Dependency Direction (high level)

```text
apps/*
  ├─> packages/reporting
  ├─> packages/cad
  ├─> packages/optimization
  ├─> packages/simulation_adapters
  ├─> packages/engineering
  └─> packages/domain

packages/reporting
  ├─> packages/cad
  ├─> packages/optimization
  ├─> packages/simulation_adapters
  ├─> packages/engineering
  └─> packages/domain

packages/cad
  ├─> packages/optimization
  ├─> packages/simulation_adapters
  ├─> packages/engineering
  └─> packages/domain

packages/optimization
  ├─> packages/simulation_adapters
  ├─> packages/engineering
  └─> packages/domain

packages/simulation_adapters
  ├─> packages/engineering
  └─> packages/domain

packages/engineering
  └─> packages/domain

packages/domain
  └─> (no internal dependencies)
```

Rule of thumb: dependencies point inward toward stable core policy (`domain`) and never outward toward app delivery layers.

---

## Module Contracts

### `apps/api`
- **Public interfaces only**
  - HTTP/JSON and/or gRPC endpoints for command/query workflows.
  - Authentication/authorization middleware contract.
  - Integration events published for async processing (e.g., `JobRequested`, `SimulationRequested`).
- **Forbidden imports**
  - Must not be imported by any `packages/*` module.
  - Must not import `apps/web` or `apps/worker`.
  - Must not import persistence ORM entities from infra-specific adapter layers directly into route handlers; use service DTOs.
- **Data exchange rules**
  - Input/output contracts are DTOs (request/response schemas), versioned at API boundary.
  - ORM entities are internal to persistence implementation and cannot cross controller boundary.
- **Ownership & review**
  - Owner: Platform/API team.
  - Required reviewers: one API owner + one domain owner when endpoint semantics change.

### `apps/worker`
- **Public interfaces only**
  - Background job handlers (`executeSimulation`, `optimizeDesign`, `generateReport`).
  - Queue subscription contract (topic names, retry policy, dead-letter behavior).
  - Job lifecycle events (`JobStarted`, `JobProgressed`, `JobCompleted`, `JobFailed`).
- **Forbidden imports**
  - Must not be imported by any `packages/*` module.
  - Must not import `apps/api` or `apps/web`.
  - Must not bypass package service contracts to call adapter internals.
- **Data exchange rules**
  - Job payloads use DTO envelopes and idempotency keys.
  - ORM entities remain internal to persistence adapters.
- **Ownership & review**
  - Owner: Compute/Operations team.
  - Required reviewers: one worker owner + one package owner for touched downstream package APIs.

### `apps/web`
- **Public interfaces only**
  - UI-facing application services/hooks (`submitDesign`, `getRunStatus`, `downloadReport`).
  - Route-level view models.
  - Client-side domain events for telemetry only.
- **Forbidden imports**
  - Must not be imported by any `packages/*` module.
  - Must not import `apps/api` or `apps/worker` runtime code (network contracts only).
  - Must not import server ORM entities.
- **Data exchange rules**
  - Uses typed DTOs from API contract package or generated client types.
  - View models may derive from DTOs but are separate UI-specific shapes.
- **Ownership & review**
  - Owner: Frontend/Product Engineering.
  - Required reviewers: one web owner + one API owner for contract changes.

### `packages/domain`
- **Public interfaces only**
  - Domain entities/value objects, pure domain services, and invariant policies.
  - Domain events (`DesignCreated`, `ConstraintViolated`, etc.) as immutable types.
  - Repository/service interfaces (ports), never concrete infra implementations.
- **Forbidden imports**
  - Cannot depend on `apps/*`.
  - Cannot depend on other `packages/*` except language/runtime standard libs.
  - Cannot import ORM frameworks, queue SDKs, HTTP frameworks.
- **Data exchange rules**
  - Domain models are not ORM models.
  - Mapping between DTOs/ORM and domain objects must happen outside domain.
- **Ownership & review**
  - Owner: Architecture/Domain team.
  - Required reviewers: two domain owners for invariant/event changes.

### `packages/engineering`
- **Public interfaces only**
  - Engineering calculation services and unit-normalization interfaces.
  - Constraint evaluation interfaces returning domain-level result objects.
  - Engineering-specific domain events where needed.
- **Forbidden imports**
  - Cannot depend on `apps/*`.
  - Cannot depend on `packages/optimization`, `packages/cad`, or `packages/reporting`.
  - Can depend only on `packages/domain` (+ standard libs).
- **Data exchange rules**
  - Inputs/outputs are typed DTO-like service contracts or domain objects, not ORM rows.
  - No persistence-layer annotations in engineering models.
- **Ownership & review**
  - Owner: Engineering Algorithms team.
  - Required reviewers: one engineering owner + one domain owner.

### `packages/simulation_adapters`
- **Public interfaces only**
  - Adapter interfaces for external solvers/simulators.
  - Canonical simulation request/response contracts.
  - Normalized simulation events and status transitions.
- **Forbidden imports**
  - Cannot depend on `apps/*`.
  - Cannot depend on `packages/optimization`, `packages/cad`, or `packages/reporting`.
  - Can depend on `packages/engineering` and `packages/domain` only.
- **Data exchange rules**
  - External vendor payloads must map into internal DTOs before entering shared packages.
  - ORM and transport-specific schemas cannot leak across adapter boundary.
- **Ownership & review**
  - Owner: Simulation Integrations team.
  - Required reviewers: one simulation owner + one engineering owner.

### `packages/optimization`
- **Public interfaces only**
  - Optimization strategy interfaces and orchestration services.
  - Objective/constraint contract definitions.
  - Optimization lifecycle events (`OptimizationIterationCompleted`, etc.).
- **Forbidden imports**
  - Cannot depend on `apps/*`.
  - Cannot depend on `packages/cad` or `packages/reporting`.
  - Can depend on `packages/simulation_adapters`, `packages/engineering`, `packages/domain` only.
- **Data exchange rules**
  - Uses optimization DTOs/domain objects; never exchanges ORM entities.
  - Persists snapshots through repository interfaces only.
- **Ownership & review**
  - Owner: Optimization team.
  - Required reviewers: one optimization owner + one simulation or engineering owner.

### `packages/cad`
- **Public interfaces only**
  - Geometry generation/transformation services.
  - CAD import/export contracts (neutral, versioned formats).
  - Geometry validation events.
- **Forbidden imports**
  - Cannot depend on `apps/*`.
  - Cannot depend on `packages/reporting`.
  - Can depend on `packages/optimization`, `packages/simulation_adapters`, `packages/engineering`, `packages/domain`.
- **Data exchange rules**
  - CAD kernels/vendors mapped to internal geometry DTOs.
  - No ORM entities in CAD API; persistence handled via repositories.
- **Ownership & review**
  - Owner: CAD/Geometry team.
  - Required reviewers: one CAD owner + one upstream owner for touched interfaces.

### `packages/reporting`
- **Public interfaces only**
  - Report composition services (summary, traceability, compliance sections).
  - Export interfaces (PDF/HTML/JSON report outputs).
  - Report lifecycle events (`ReportGenerated`, `ReportPublished`).
- **Forbidden imports**
  - Cannot depend on `apps/*`.
  - Should remain leaf-like in package layer: no package may depend on reporting for core logic.
  - May depend on `packages/cad`, `packages/optimization`, `packages/simulation_adapters`, `packages/engineering`, `packages/domain`.
- **Data exchange rules**
  - Report templates consume DTO projections, not ORM entities.
  - Read models for reporting are separate from transactional domain aggregates.
- **Ownership & review**
  - Owner: Reporting/Customer Output team.
  - Required reviewers: one reporting owner + one producer-package owner of any new data projection.

---

## Data Exchange Canonical Rules (DTO vs ORM Separation)

1. **No ORM types across package/app public boundaries.**
2. **All boundary contracts are explicit DTOs or domain objects** with semantic names and versioning where externally consumed.
3. **Mapping layers are mandatory**:
   - Transport DTO ⇄ Application DTO
   - Application DTO ⇄ Domain model
   - Domain model ⇄ Persistence ORM entity
4. **Events are immutable contracts** and must not embed ORM models.
5. **Schema evolution policy**: additive-first changes; breaking contract changes require version bump and migration note.

---

## Allowed Dependency Matrix

Legend: ✅ allowed dependency, ❌ forbidden dependency.

| From \ To | apps/api | apps/worker | apps/web | domain | engineering | simulation_adapters | optimization | cad | reporting |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| **apps/api** | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **apps/worker** | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **apps/web** | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **packages/domain** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **packages/engineering** | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **packages/simulation_adapters** | ❌ | ❌ | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ |
| **packages/optimization** | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| **packages/cad** | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ |
| **packages/reporting** | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ |

Enforcement recommendation: codify these rules with static import lints and CI checks to prevent architectural drift.
