import argparse
import json
import logging
import time
from packages.domain.repositories.jobs import JobRepository
from packages.domain.schemas.common import JobStatus
from packages.domain.services.pipeline import run_generation_pipeline
from packages.domain.schemas.requirements import RequirementInput
from packages.domain.scoring.recalibrate import recalibrate_policy
from packages.reporting.explain import build_explainability_report
from apps.api.settings import get_settings

logger = logging.getLogger("dust.worker")


def process_one_job(repo: JobRepository, job_id: str | None = None):
    job_id = job_id or repo.next_queued()
    if not job_id:
        return False
    job = repo.get(job_id)
    if not job or job["status"] != JobStatus.queued.value:
        return False
    repo.update(job_id, status=JobStatus.running.value, progress=0.1)
    logger.info(json.dumps({"event": "job_started", "job_id": job_id, "trace_id": job["trace_id"], "request_id": job["request_id"]}))
    try:
        req = RequirementInput(**job["normalized_input"])
        repo.update(job_id, progress=0.5)
        settings = get_settings()
        result = run_generation_pipeline(
            req,
            sim_enabled=settings.sim_adapter_enabled,
            cad_enabled=settings.cad_adapter_enabled,
            toolchain_enabled=settings.toolchain_adapter_enabled,
        )
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


def run_scheduled_recalibration(feedback_path: str, benchmark_path: str, output_dir: str = "artifacts/policy-proposals", min_sample_size: int = 20) -> dict:
    proposal = recalibrate_policy(
        feedback_path=feedback_path,
        benchmark_path=benchmark_path,
        output_dir=output_dir,
        min_sample_size=min_sample_size,
    )
    logger.info(json.dumps({"event": "recalibration_generated", "decision": proposal["meta"]["decision"], "sample_size": proposal["meta"]["sample_size"]}))
    return proposal


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dust worker utilities")
    parser.add_argument("--run-recalibration", action="store_true", help="Run scheduled policy recalibration")
    parser.add_argument("--feedback-path", default="artifacts/telemetry/feedback.json")
    parser.add_argument("--benchmark-path", default="artifacts/telemetry/benchmarks.json")
    parser.add_argument("--output-dir", default="artifacts/policy-proposals")
    parser.add_argument("--min-sample-size", type=int, default=20)
    args = parser.parse_args()

    if args.run_recalibration:
        print(json.dumps(run_scheduled_recalibration(args.feedback_path, args.benchmark_path, args.output_dir, args.min_sample_size), indent=2))
