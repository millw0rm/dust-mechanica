from fastapi import APIRouter, Header, HTTPException
import sqlite3
from pydantic import BaseModel
from packages.domain.repositories.jobs import JobRepository
from packages.domain.schemas.requirements import RequirementInput
from packages.domain.schemas.responses import CandidateGenerationResponse, JobDetailResponse, FeedbackRequest, TelemetrySlicesResponse, TelemetryDriftResponse
from packages.domain.schemas.common import JobStatus
from packages.domain.services.pipeline import run_generation_pipeline

router = APIRouter(prefix="/v1", tags=["candidates"])
repo = JobRepository()


class GenerateRequest(BaseModel):
    requirement: RequirementInput
    async_mode: bool = False
    allowed_topologies: list[str] | None = None
    excluded_topologies: list[str] | None = None
    explain_topology_selection: bool = False
    toolchain_enabled: bool = True


@router.post('/candidates/generate')
def generate(payload: GenerateRequest, x_request_id: str | None = Header(default=None), x_trace_id: str | None = Header(default=None), idempotency_key: str | None = Header(default=None)):
    if payload.async_mode:
        existing = repo.find_by_idempotency_key(idempotency_key or x_request_id or "")
        if existing:
            return {"schema_version": "2.0", "job_id": existing["id"], "status": existing["status"], "idempotent_replay": True}
        v = {"issues": [], "missing": [], "conflicts": []}
        job_id = repo.create(payload.requirement.model_dump(), v, x_trace_id or "", idempotency_key or x_request_id or "")
        return {"schema_version": "2.0", "job_id": job_id, "status": "queued"}
    result = run_generation_pipeline(payload.requirement, allowed_topologies=payload.allowed_topologies, excluded_topologies=payload.excluded_topologies, explain_topology_selection=payload.explain_topology_selection, toolchain_enabled=payload.toolchain_enabled)
    return CandidateGenerationResponse(**result)


@router.get('/jobs/{id}', response_model=JobDetailResponse)
def job_status(id: str):
    job = repo.get(id)
    if not job:
        raise HTTPException(status_code=404, detail="job not found")
    result = CandidateGenerationResponse(**job["result"]) if job.get("result") else None
    return JobDetailResponse(schema_version="2.0", id=id, status=job["status"], progress=job["progress"], created_at=job["created_at"], updated_at=job["updated_at"], completed_at=job["completed_at"], error=job["error"], result=result, review=job.get("review"), report=job.get("report"))


@router.post('/jobs/{id}/approve')
def approve_job(id: str, note: str = "", reason: str = ""):
    job = repo.get(id)
    if not job:
        raise HTTPException(404, "job not found")
    if job["status"] != JobStatus.awaiting_review.value:
        raise HTTPException(409, "invalid transition")
    repo.update(id, status=JobStatus.approved.value, review={"status": "approved", "note": note, "reason": reason})
    return {"id": id, "status": "approved"}


@router.post('/jobs/{id}/reject')
def reject_job(id: str, reason: str, rerun_hint: str = ""):
    job = repo.get(id)
    if not job:
        raise HTTPException(404, "job not found")
    if job["status"] != JobStatus.awaiting_review.value:
        raise HTTPException(409, "invalid transition")
    if not reason:
        raise HTTPException(400, "reason required")
    repo.update(id, status=JobStatus.rejected.value, review={"status": "rejected", "reason": reason, "rerun_hint": rerun_hint})
    return {"id": id, "status": "rejected"}


@router.get('/jobs/{id}/design-review-package')
def design_review_package(id: str):
    job = repo.get(id)
    if not job:
        raise HTTPException(404, "job not found")
    if job["status"] != JobStatus.approved.value:
        raise HTTPException(409, "only approved jobs can be exported")
    result = job.get("result") or {}
    return {
        "job_id": id,
        "ranked_candidates": result.get("candidates", []),
        "assumptions": result.get("assumptions", {}),
        "risk_flags": [c.get("risk_flags", []) for c in result.get("candidates", [])],
        "sensitivity": [c.get("robustness") for c in result.get("candidates", [])],
        "simulation_summary": [c.get("simulation_summary") for c in result.get("candidates", [])],
        "cad_handoff_artifact_refs": [c.get("cad_artifact_ref") for c in result.get("candidates", [])],
        "sourcing_highlights": [c.get("score_breakdown", {}).get("sourcing_risk") for c in result.get("candidates", [])],
        "lead_time_highlights": [c.get("score_breakdown", {}).get("lead_time_impact") for c in result.get("candidates", [])],
        "approval_status": job.get("review", {}).get("status"),
        "reviewer_notes": job.get("review"),
    }


@router.post('/jobs/{id}/feedback')
def submit_feedback(id: str, payload: FeedbackRequest):
    job = repo.get(id)
    if not job:
        raise HTTPException(404, "job not found")
    allowed_states = {JobStatus.approved.value, JobStatus.completed.value}
    if job["status"] not in allowed_states:
        raise HTTPException(
            status_code=409,
            detail={
                "message": "feedback not allowed for current job status",
                "job_id": id,
                "current_status": job["status"],
                "allowed_statuses": sorted(allowed_states),
            },
        )
    if not repo.is_feedback_window_open(job):
        raise HTTPException(
            status_code=409,
            detail={
                "message": "feedback window expired",
                "job_id": id,
                "completed_at": job.get("completed_at"),
                "window_days": repo.feedback_window_days(),
            },
        )
    try:
        repo.add_feedback(id, payload.model_dump())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"message": str(exc), "job_id": id}) from exc
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail={"message": "duplicate feedback", "job_id": id}) from exc
    return {"job_id": id, "recorded": True}


@router.get('/telemetry/summary')
def telemetry_summary():
    return {"schema_version": "2.1", **repo.feedback_summary()}


@router.get('/telemetry/slices', response_model=TelemetrySlicesResponse)
def telemetry_slices(bucket: str = "daily"):
    try:
        slices = repo.telemetry_slices(bucket=bucket)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TelemetrySlicesResponse(bucket=bucket, slices=slices)


@router.get('/telemetry/drift', response_model=TelemetryDriftResponse)
def telemetry_drift(recent_days: int = 7, baseline_days: int = 28):
    if recent_days <= 0 or baseline_days <= 0:
        raise HTTPException(status_code=400, detail="window sizes must be positive")
    return TelemetryDriftResponse(**repo.telemetry_drift(recent_days=recent_days, baseline_days=baseline_days))
