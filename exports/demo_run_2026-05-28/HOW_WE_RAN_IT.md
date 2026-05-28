# Demo run procedure (2026-05-28)

## Goal
Run the current generation pipeline on the sample linear-axis request and export artifacts.

## Commands used
1. Install missing dependency:
   - `pip install pyyaml`
2. Execute the pipeline directly from Python:
   - loads `examples/sample_request_linear_axis.json`
   - calls `run_generation_pipeline(req, explain_topology_selection=True)`
   - writes outputs to this directory.

## Artifacts
- `request.json` - normalized input payload used for this run
- `response.json` - full pipeline output (ranked candidates + assumptions + flags)
- `summary.json` - compact summary (candidate count, top candidate id, issues/conflicts)
