from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field
from packages.domain.repositories.jobs import JobRepository
from packages.domain.schemas.requirements import RequirementInput
from packages.domain.schemas.responses import CandidateGenerationResponse, JobDetailResponse
from packages.domain.services.pipeline import run_generation_pipeline

router = APIRouter(prefix="/v1", tags=["candidates"])
repo = JobRepository()


class GenerateRequest(BaseModel):
    requirement: RequirementInput
    async_mode: bool = False
    allowed_topologies: list[str] | None = None
    excluded_topologies: list[str] | None = None
    explain_topology_selection: bool = False


@router.post('/candidates/generate')
def generate(payload: GenerateRequest, x_request_id: str | None = Header(default=None), x_trace_id: str | None = Header(default=None), idempotency_key: str | None = Header(default=None)):
    if payload.async_mode:
        existing = repo.find_by_idempotency_key(idempotency_key or x_request_id or "")
        if existing:
            return {"schema_version": "2.0", "job_id": existing["id"], "status": existing["status"], "idempotent_replay": True}
        v = {"issues": [], "missing": [], "conflicts": []}
        job_id = repo.create(payload.requirement.model_dump(), v, x_trace_id or "", idempotency_key or x_request_id or "")
        return {"schema_version": "2.0", "job_id": job_id, "status": "queued"}
    result = run_generation_pipeline(payload.requirement, allowed_topologies=payload.allowed_topologies, excluded_topologies=payload.excluded_topologies, explain_topology_selection=payload.explain_topology_selection)
    return CandidateGenerationResponse(**result)


@router.get('/jobs/{id}', response_model=JobDetailResponse)
def job_status(id: str):
    job = repo.get(id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    result = CandidateGenerationResponse(**job["result"]) if job.get("result") else None
    return JobDetailResponse(schema_version="2.0", id=id, status=job["status"], progress=job["progress"], created_at=job["created_at"], updated_at=job["updated_at"], completed_at=job["completed_at"], error=job["error"], result=result, review=job.get("review"), report=job.get("report"))
