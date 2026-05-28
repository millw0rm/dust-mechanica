# Recalibration workflow

## Goal
Create a repeatable calibration process that proposes scoring and policy updates from collected outcomes while requiring explicit human approval prior to activation.

## Inputs
- Feedback telemetry JSON (example schema: lead-time error, risk miss, observed margin, observed efficiency).
- Benchmark comparison JSON (expected vs observed feasibility).

## Scheduled trigger
Use the worker utility:

```bash
python -m apps.worker.runner --run-recalibration \
  --feedback-path artifacts/telemetry/feedback.json \
  --benchmark-path artifacts/telemetry/benchmarks.json \
  --output-dir artifacts/policy-proposals \
  --min-sample-size 20
```

## Proposal artifacts
- Candidate proposal metadata and review state: `artifacts/policy-proposals/latest.json`
- Candidate policy payload: `packages/engineering/policy/v2/candidate.scoring.json`

If sample size is below threshold, no candidate policy is generated and decision is marked `no_op_insufficient_sample`.

## Human review gate
All proposals are created with:
- `review_gate.status = pending_human_review`
- `review_gate.approved = false`

Promotion is a separate explicit step (human-in-the-loop) using the promotion helper.

## Promotion procedure
1. Review `artifacts/policy-proposals/latest.json` candidate metrics and update rationale.
2. Record approver and notes.
3. Promote candidate to active v2 policy (`packages/engineering/policy/v2/scoring.yaml`).
4. Update deployment/configuration to consume policy version `v2`.

## Rollback procedure
1. Revert policy loader configuration back to `v1`.
2. Archive failed proposal by moving `artifacts/policy-proposals/latest.json` to a timestamped file.
3. Open a postmortem with observed regressions and retain telemetry for next recalibration cycle.
