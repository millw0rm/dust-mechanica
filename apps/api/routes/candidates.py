from fastapi import APIRouter
from packages.domain.schemas.requirements import RequirementInput
from packages.domain.schemas.jobs import JobStatusResponse
from packages.domain.services.pipeline import run_generation_pipeline

router = APIRouter(prefix="/v1", tags=["candidates"])


@router.post('/candidates/generate')
def generate(req: RequirementInput):
    result = run_generation_pipeline(req)
    return {"candidates": result["candidates"], "issues": result["issues"], "missing": result["missing"], "conflicts": result["conflicts"]}


@router.get('/jobs/{id}', response_model=JobStatusResponse)
def job_status(id: str):
    return JobStatusResponse(id=id, status="running", progress=0.4)
