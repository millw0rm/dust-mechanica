from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from packages.domain.repositories.jobs import JobRepository
from packages.domain.schemas.requirements import RequirementInput
from packages.domain.schemas.responses import CandidateGenerationResponse, JobDetailResponse
from packages.domain.services.pipeline import run_generation_pipeline

router = APIRouter(prefix="/v1", tags=["candidates"])
repo = JobRepository()


class GenerateRequest(BaseModel):
    requirement: RequirementInput
    async_mode: bool = False


@router.post('/candidates/generate')
def generate(req: RequirementInput, async_mode: bool = False, x_request_id: str | None = Header(default=None), x_trace_id: str | None = Header(default=None)):
    if async_mode:
        v = {"issues": [], "missing": [], "conflicts": []}
        job_id = repo.create(req.model_dump(), v, x_trace_id or "", x_request_id or "")
        return {"schema_version": "2.0", "job_id": job_id, "status": "queued"}
    result = run_generation_pipeline(req)
    return CandidateGenerationResponse(**result)


@router.get('/jobs/{id}', response_model=JobDetailResponse)
def job_status(id: str):
    job = repo.get(id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    result = CandidateGenerationResponse(**job["result"]) if job.get("result") else None
    return JobDetailResponse(schema_version="2.0", id=id, status=job["status"], progress=job["progress"], created_at=job["created_at"], updated_at=job["updated_at"], completed_at=job["completed_at"], error=job["error"], result=result)
