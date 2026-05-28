import json
import logging
import time
from packages.domain.repositories.jobs import JobRepository
from packages.domain.schemas.common import JobStatus
from packages.domain.services.pipeline import run_generation_pipeline
from packages.domain.schemas.requirements import RequirementInput
from packages.reporting.explain import build_explainability_report
from apps.api.settings import get_settings

logger = logging.getLogger("dust.worker")


def process_one_job(repo: JobRepository):
    job_id = repo.next_queued()
    if not job_id:
        return False
    job = repo.get(job_id)
    repo.update(job_id, status=JobStatus.running.value, progress=0.1)
    logger.info(json.dumps({"event": "job_started", "job_id": job_id, "trace_id": job["trace_id"], "request_id": job["request_id"]}))
    try:
        req = RequirementInput(**job["normalized_input"])
        repo.update(job_id, progress=0.5)
        settings = get_settings()
        result = run_generation_pipeline(req, sim_enabled=settings.sim_adapter_enabled, cad_enabled=settings.cad_adapter_enabled)
        if repo.get(job_id).get("cancelled"):
            repo.update(job_id, status=JobStatus.failed.value, progress=1.0, error="cancelled")
            return True
        report = build_explainability_report(result)
        repo.update(job_id, status=JobStatus.awaiting_review.value, progress=1.0, result=result, report=report)
        logger.info(json.dumps({"event": "job_completed", "job_id": job_id, "trace_id": job["trace_id"], "request_id": job["request_id"]}))
    except Exception as exc:
        repo.update(job_id, status=JobStatus.failed.value, progress=1.0, error=str(exc))
        logger.error(json.dumps({"event": "job_failed", "job_id": job_id, "trace_id": job["trace_id"], "request_id": job["request_id"], "error": str(exc)}))
    return True


def worker_loop(repo: JobRepository, sleep_seconds: float = 0.2):
    while True:
        had = process_one_job(repo)
        if not had:
            time.sleep(sleep_seconds)
