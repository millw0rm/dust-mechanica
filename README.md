# Dust Mechanica

Minimal Week 1 monorepo slice for a belt-driven linear axis topology with schema-first contracts and API endpoints.


## Async candidate generation

```bash
curl -X POST "http://localhost:8000/v1/candidates/generate?async_mode=true" \
  -H "content-type: application/json" \
  -d @examples/sample_request_linear_axis.json
```

Then poll:

```bash
curl http://localhost:8000/v1/jobs/<job_id>
```


## Multi-topology quickstart
Use `/v1/candidates/generate` request body with `allowed_topologies`, `excluded_topologies`, and `explain_topology_selection`.
