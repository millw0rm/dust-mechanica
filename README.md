# Dust Mechanica

AI-assisted multidisciplinary engineering design platform roadmap.

## Vision
Dust Mechanica will function as a "virtual full-stack engineering team" that combines:
- Electrical engineering (motors, drives, power, sensing)
- Mechanical engineering (kinematics, strength, vibration, thermal, manufacturability)
- Software/controls engineering (control logic, optimization, diagnostics)

Given high-level requirements, the platform should propose design candidates, validate them through analytical and simulation workflows, optimize trade-offs, and produce build-ready outputs.

## Product Scope (V1)
Start with a constrained domain:
- Electromechanical motion systems (linear/rotary axes, conveyor drives, indexing units)

Rationale:
- Broad enough to be useful
- Narrow enough for practical delivery and validation

## Core Inputs
The system should accept guided-form + natural-language requirements across:
- Functional targets (speed, torque/force, range/stroke, accuracy, backlash, duty cycle)
- Load profile (mass, inertia, external forces, shock/vibration)
- Environment (temperature, humidity, dust/IP, corrosion)
- Constraints (envelope, weight, budget, power source, materials, manufacturing)
- Controls requirements (mode, response/overshoot/error, communication bus)
- Optimization priorities (cost/mass/efficiency/reliability/noise/compactness)
- Compliance expectations (ISO/IEC/UL and domain-specific constraints)

## Architecture Blueprint
1. **Requirements Parser**
   - Parse NL + form input into strict typed schema (units-aware)
   - Detect missing/conflicting constraints
2. **Knowledge + Component Layer**
   - Catalogs: motors, drives, bearings, gears, belts, screws, sensors, materials
   - Compatibility and derating rules
3. **Mechanism/Topology Synthesizer**
   - Candidate generation: direct drive, belt, gear, lead screw, etc.
4. **Physics & Simulation Layer**
   - First-pass analytical checks (fast)
   - Deep simulation adapters (MBD/FEA/thermal/control)
5. **Optimization Layer**
   - Multi-objective optimization (Pareto frontier)
6. **CAD/BOM/Reporting Layer**
   - Parametric CAD export
   - BOM + cost estimate
   - Engineering report with assumptions, margins, risks
7. **Verification & Sign-off Layer**
   - Confidence score, uncertainty bounds, human sign-off gates


## AI Agent Architecture (Planned)
Dust Mechanica will use a supervised multi-agent pattern with strict guardrails:
- Requirement Interpreter Agent
- Concept Synthesis Agent
- Simulation Orchestrator Agent
- Optimization Agent
- Verification & Safety Agent
- Report Generator Agent

Design decisions remain human-supervised with mandatory approval gates.
See `docs/ai-system-design.md` for role definitions, orchestration flow, guardrails, and traceability model.

## Proposed Tech Stack
- Backend: Python + FastAPI
- Data models: Pydantic
- Numerics: NumPy, SciPy, Pint
- Optimization: Optuna or pymoo
- CAD: FreeCAD Python API
- Simulation adapters: Modelica/MBDyn/CalculiX wrappers
- Storage: PostgreSQL
- Queue: Celery or RQ
- Frontend: React + Plotly

## 8-Week Delivery Plan
### Sprint 1 (Weeks 1-2): Foundations
- API scaffold, schema, unit normalization, validation engine, DB models

### Sprint 2 (Weeks 3-4): Feasibility MVP
- Topology library (3-5 options)
- First-pass sizing equations
- Candidate ranking + comparison view

### Sprint 3 (Weeks 5-6): Optimization + Async
- Optimization service
- Constraint/objective framework
- Background job orchestration
- Pareto visualization API/UI

### Sprint 4 (Weeks 7-8): CAD/BOM/Report v1
- Parametric CAD for initial topologies
- STEP/STL export
- BOM + cost model
- Downloadable engineering report bundle

## MVP Outputs Per Candidate
- Mechanism concept diagram/topology
- Selected components and rationale
- Performance estimates (speed/torque/efficiency)
- Safety margins and key pass/fail checks
- CAD artifacts (where available)
- BOM and preliminary cost
- Prototype checklist

## Safety Position
This platform is decision-support, not autonomous certification.
Every generated design must include:
- Explicit assumptions
- Confidence/uncertainty annotations
- Risk flags
- Human engineering sign-off for safety-critical deployments

## Suggested Initial Repository Structure
- `apps/api` - orchestration and APIs
- `apps/worker` - background optimization/simulation tasks
- `apps/web` - UX for requirement entry and tradeoff views
- `packages/domain` - synthesis + scoring core logic
- `packages/engineering` - mechanical/electrical/controls calculators
- `packages/simulation_adapters` - solver connectors
- `packages/optimization` - objective/constraint/search code
- `packages/cad` - CAD generation and export
- `packages/reporting` - reporting and sign-off outputs

## Next Build Steps
1. Implement V1 requirement schema and validation contract
2. Seed component catalogs and compatibility rules
3. Build candidate synthesis with analytical feasibility scoring
4. Add optimization run pipeline
5. Integrate CAD/BOM/report generation
6. Add deep simulation and reliability expansion
