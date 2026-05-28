from apps.worker.runner import process_one_job
from packages.domain.repositories.jobs import JobRepository


def test_failed_job_path(tmp_path):
    repo = JobRepository(path=str(tmp_path / 'jobs.db'))
    job_id = repo.create({"bad":"input"}, {}, "t", "r")
    process_one_job(repo)
    job = repo.get(job_id)
    assert job["status"] == "failed"
    assert job["error"]
