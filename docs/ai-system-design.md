# AI System Design (V1)

This document defines how AI is used inside Dust Mechanica as a supervised, auditable engineering copilot system.

## Goals
- Translate user intent into verifiable engineering specifications
- Generate multiple feasible design concepts
- Coordinate simulation and optimization workflows
- Explain tradeoffs and risks clearly
- Keep human engineers in control for final sign-off

## Multi-Agent Roles

### 1) Requirement Interpreter Agent
**Purpose:** Convert natural-language requests and form inputs into typed, unit-aware requirement objects.

**Inputs:** user prompt, guided form values, prior project context

**Outputs:** normalized `RequirementSpec`, ambiguity flags, missing-field prompts

**Guardrails:**
- Never infer safety-critical values silently
- Require explicit user confirmation for defaults affecting load/safety/compliance

### 2) Concept Synthesis Agent
**Purpose:** Propose candidate topologies and component combinations.

**Inputs:** validated requirements + component catalog + compatibility rules

**Outputs:** ranked `CandidateDesign[]` with rationale and assumptions

**Guardrails:**
- Enforce compatibility and envelope constraints
- Emit rejection reasons for invalid concepts

### 3) Simulation Orchestrator Agent
**Purpose:** Select and execute appropriate analysis tiers.

**Inputs:** candidate designs, load cases, environment profiles

**Outputs:** simulation job specs, parsed KPIs, confidence tags

**Guardrails:**
- Run fast analytical checks before expensive solvers
- Mark outputs as preliminary when high-fidelity simulation is unavailable

### 4) Optimization Agent
**Purpose:** Search design space for Pareto-optimal solutions.

**Inputs:** variable bounds, objectives, constraints, candidate seeds

**Outputs:** Pareto set, sensitivity insights, dominated/non-dominated labels

**Guardrails:**
- Preserve hard constraints as non-negotiable
- Track reproducibility (seed, versioned formulas, solver config)

### 5) Verification & Safety Agent
**Purpose:** Validate margins, assumptions, and compliance mappings.

**Inputs:** optimized candidates + simulation/analytical outputs

**Outputs:** pass/fail checklist, risk register, required human approvals

**Guardrails:**
- No "safe" verdict without complete mandatory checks
- Highlight model limitations and uncertainty bounds

### 6) Report Generator Agent
**Purpose:** Produce user-ready engineering packages.

**Inputs:** final candidate package + verification artifacts

**Outputs:** design summary, BOM, CAD pointers, assumptions, next prototype actions

**Guardrails:**
- Include traceability links to calculations and solver runs
- Separate facts, assumptions, and recommendations clearly

## Agent Orchestration Flow
1. Intake request and normalize units
2. Resolve missing/conflicting requirements
3. Generate candidate concepts
4. Run analytical feasibility filters
5. Run optimization loop
6. Trigger deep simulation for top candidates
7. Run verification/safety checks
8. Generate report and request human sign-off

## Tool Access and Boundaries
- Requirement Interpreter: schema validators, unit converter, requirement history
- Synthesis Agent: topology library, component catalog, compatibility engine
- Simulation Agent: analytical solver + MBD/FEA adapters
- Optimization Agent: objective/constraint library, optimization backend
- Verification Agent: standards mapping, checklist engine, risk policy rules
- Report Agent: templating engine, artifact storage, export pipeline

No agent should bypass policy checks or directly mark a design production-ready.

## Memory and Context Strategy
- **Project memory:** persistent project specs, approved assumptions, past runs
- **Session memory:** temporary context for active design iteration
- **Artifact memory:** immutable references to CAD, simulation, and report outputs

All major decisions should be attached to:
- source inputs
- model/tool version
- timestamp
- responsible agent

## Human-in-the-Loop Control Points
Mandatory approvals:
1. Requirement freeze before optimization
2. Candidate shortlist before deep simulation budget spend
3. Pre-prototype safety review
4. Final engineering sign-off before release/manufacture

## Risk and Failure Handling
- Detect contradictory requirements and block progression
- Fall back to conservative assumptions when non-critical values are missing
- Escalate to user/engineer when uncertainty exceeds threshold
- Log solver failures with actionable retry guidance

## Traceability and Audit
For each final recommendation, store:
- requirement snapshot
- candidate generation rationale
- solver outputs and key KPIs
- optimization configuration and results
- verification checklist outcomes
- sign-off metadata

## MVP Implementation Sequence
1. Build Requirement Interpreter + typed schema contracts
2. Implement Concept Synthesis on 3-5 topologies
3. Add analytical feasibility + scoring
4. Integrate optimization and Pareto output
5. Add verification checklist + risk register
6. Add report generation with full traceability
