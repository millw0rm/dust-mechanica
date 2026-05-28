# Demo Week 1

## Run
- `python -m pytest`
- `uvicorn apps.api.main:app --reload`

## Validate Request
`curl -X POST localhost:8000/v1/requirements/validate -H 'content-type: application/json' -d @examples/sample_request_linear_axis.json`

## Generate Candidates
`curl -X POST localhost:8000/v1/candidates/generate -H 'content-type: application/json' -d @examples/sample_request_linear_axis.json`
