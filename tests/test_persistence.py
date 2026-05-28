from packages.domain.repositories.jobs import JobRepository


def test_persistence_round_trip(tmp_path):
    repo = JobRepository(path=str(tmp_path / 'jobs.db'))
    job_id = repo.create({"a":1}, {"issues":[]}, "t1", "r1")
    repo.update(job_id, status="running", progress=0.4)
    job = repo.get(job_id)
    assert job["status"] == "running"
    assert job["progress"] == 0.4
