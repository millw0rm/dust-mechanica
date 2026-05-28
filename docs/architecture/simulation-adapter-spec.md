# Simulation Adapter Specification

This document defines the **minimum contract** for simulation adapters that bridge domain requests and external solvers/runtimes.

## 1) Adapter interface

Each adapter MUST implement four methods:

```ts
interface SimulationAdapter<DomainInput, DomainOutput> {
  prepare(input: DomainInput, context: AdapterContext): Promise<PreparedRun>;
  run(prepared: PreparedRun, context: AdapterContext): Promise<RawSolverResult>;
  parse(raw: RawSolverResult, context: AdapterContext): Promise<ParsedResult>;
  mapToDomain(parsed: ParsedResult, context: AdapterContext): Promise<DomainOutput>;
}
```

### Method responsibilities

- `prepare(...)`
  - Validate domain input shape and units.
  - Build solver-native input artifacts (files/payloads/CLI args).
  - Return immutable run metadata (working dir, expected outputs, solver options).
- `run(...)`
  - Execute the solver process/job only.
  - Enforce sandbox/time limits.
  - Return raw artifacts (stdout/stderr/exit code/output files).
- `parse(...)`
  - Parse raw artifacts into typed intermediate structures.
  - Normalize units and coordinate frames where needed.
  - Detect malformed or incomplete solver output.
- `mapToDomain(...)`
  - Map parsed data to canonical domain DTOs.
  - Populate uncertainty/quality metadata when available.
  - Avoid leaking solver-specific types outside the adapter boundary.

---

## 2) Capability flags

Adapters expose capabilities for planning/routing:

```ts
interface AdapterCapabilities {
  thermal: boolean;
  vibration: boolean;
  controls: boolean;
  nonlinear: boolean;
  runtimeProfile: 'interactive' | 'batch' | 'long_running';
}
```

### Semantics

- `thermal`: Supports thermal analysis outputs (e.g., temperatures, heat flux).
- `vibration`: Supports modal/frequency or transient vibration analysis.
- `controls`: Supports control-system or closed-loop simulation behavior.
- `nonlinear`: Supports materially/geometrically nonlinear solution paths.
- `runtimeProfile`:
  - `interactive`: expected completion in seconds.
  - `batch`: expected completion in minutes.
  - `long_running`: may take tens of minutes to hours and must be queued.

---

## 3) Canonical input/output mapping

Adapters translate between canonical domain DTOs and solver-native schemas.

### Canonical input DTO (example)

```ts
interface SimulationRequestDTO {
  requestId: string;
  modelRef: string;
  scenario: {
    type: 'thermal' | 'vibration' | 'controls' | 'multiphysics';
    parameters: Record<string, number | string | boolean>;
  };
  constraints: Record<string, unknown>;
  units: 'SI' | 'US_CUSTOMARY';
  timeLimitSec?: number;
}
```

### Canonical output DTO (example)

```ts
interface SimulationResultDTO {
  requestId: string;
  status: 'ok' | 'error';
  metrics: Record<string, number>;
  series?: Record<string, Array<{ t: number; value: number }>>;
  artifacts: Array<{ kind: string; uri: string }>;
  diagnostics: {
    warnings: string[];
    solverVersion?: string;
    elapsedMs?: number;
  };
}
```

### Mapping expectations

- Input mapping:
  - Canonical DTO → solver deck/config/payload.
  - All unit conversions are explicit and testable.
  - Default values are applied in one place (`prepare`).
- Output mapping:
  - Solver-native outputs → typed parsed structures (`parse`).
  - Parsed structures → `SimulationResultDTO` (`mapToDomain`).
  - Missing optional outputs SHOULD produce warnings, not hard failures.

---

## 4) Error classification

Adapters MUST normalize failures to one of:

- `input_invalid`
  - Invalid DTO shape, impossible parameter ranges, unsupported scenario/options.
- `solver_failure`
  - Nonzero exit codes, crashed process, missing required output artifacts.
- `timeout`
  - Worker or solver exceeded time limit/cancellation deadline.
- `numerical_instability`
  - Divergence, non-convergence, NaN/Inf propagation, ill-conditioned solve.

Suggested error envelope:

```ts
interface AdapterError {
  code: 'input_invalid' | 'solver_failure' | 'timeout' | 'numerical_instability';
  message: string;
  retryable: boolean;
  details?: Record<string, unknown>;
}
```

Retry guidance:

- `input_invalid`: not retryable without input change.
- `solver_failure`: sometimes retryable (infra/transient conditions).
- `timeout`: retryable with larger budget or lower model fidelity.
- `numerical_instability`: retryable only with modified numerics/step settings.

---

## 5) Sandbox and time-limit expectations

Worker execution for `run(...)` MUST follow these rules:

- Process isolation: solver runs in an isolated worker environment (container/VM/sandbox).
- Filesystem scope: read/write only within assigned working directory and allowed mounts.
- Network policy: default deny egress unless explicitly allowed by adapter policy.
- Resource ceilings:
  - CPU and memory limits are configured per job class.
  - Ephemeral disk quota must be enforced.
- Time limits:
  - Hard wall-clock timeout MUST terminate execution.
  - Soft warning threshold SHOULD emit progress/heartbeat warnings.
- Cancellation:
  - Worker MUST support cooperative cancellation and forced kill fallback.
- Observability:
  - Capture stdout/stderr, exit status, elapsed time, peak memory when available.
  - Persist run manifest with deterministic artifact paths.

---

## Minimal stub adapter template

```ts
export class StubSimulationAdapter
  implements SimulationAdapter<SimulationRequestDTO, SimulationResultDTO>
{
  capabilities: AdapterCapabilities = {
    thermal: true,
    vibration: false,
    controls: false,
    nonlinear: false,
    runtimeProfile: 'interactive',
  };

  async prepare(input: SimulationRequestDTO): Promise<PreparedRun> {
    // Validate + map canonical input into solver-native payload.
    return { workDir: '/tmp/stub', payload: { ...input } } as PreparedRun;
  }

  async run(prepared: PreparedRun): Promise<RawSolverResult> {
    // Execute sandboxed command with timeout.
    return { exitCode: 0, stdout: 'ok', stderr: '', files: [] } as RawSolverResult;
  }

  async parse(raw: RawSolverResult): Promise<ParsedResult> {
    // Parse solver outputs into typed intermediate form.
    return { metrics: { sample: 1.0 } } as ParsedResult;
  }

  async mapToDomain(parsed: ParsedResult): Promise<SimulationResultDTO> {
    // Convert parsed data to canonical domain DTO.
    return {
      requestId: 'stub',
      status: 'ok',
      metrics: parsed.metrics,
      artifacts: [],
      diagnostics: { warnings: [] },
    };
  }
}
```
