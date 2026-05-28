# Benchmark Scenario Spec

Each scenario in `examples/benchmarks/scenarios.json` includes:
- `id`, `kind`, `requirement`, and `expected`.
- `expected.feasible`, `expected.topology_family`, and `expected.risk_classes`.

Acceptance criteria:
- Calibration harness runs all scenarios deterministically.
- Summary reports pass-rate, ranking stability, and mismatch categories.
- Failing scenarios list explicit mismatch reasons.
