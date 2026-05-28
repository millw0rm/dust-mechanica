import json
import sqlite3
import threading
import uuid
from datetime import datetime, timezone
from packages.domain.schemas.common import JobStatus


def utcnow():
    return datetime.now(timezone.utc).isoformat()


class JobRepository:
    def __init__(self, path: str = "./.data/jobs.db"):
        self.path = path
        self._lock = threading.Lock()
        self._init_db()

    def _conn(self):
        return sqlite3.connect(self.path)

    def _init_db(self):
        import os
        os.makedirs("./.data", exist_ok=True)
        with self._conn() as c:
            c.execute(
                """create table if not exists jobs (
                id text primary key, status text, progress real,
                normalized_input text, validation text, result text,
                error text, trace_id text, request_id text,
                created_at text, updated_at text, completed_at text
                )"""
            )

    def create(self, normalized_input: dict, validation: dict, trace_id: str, request_id: str):
        job_id = str(uuid.uuid4())
        now = utcnow()
        with self._lock, self._conn() as c:
            c.execute("insert into jobs values (?,?,?,?,?,?,?,?,?,?,?,?)", (
                job_id, JobStatus.queued.value, 0.0, json.dumps(normalized_input), json.dumps(validation), None,
                None, trace_id, request_id, now, now, None,
            ))
        return job_id

    def update(self, job_id: str, *, status=None, progress=None, result=None, error=None):
        sets = ["updated_at=?"]
        args = [utcnow()]
        if status is not None:
            sets.append("status=?")
            args.append(status)
        if progress is not None:
            sets.append("progress=?")
            args.append(progress)
        if result is not None:
            sets.append("result=?")
            args.append(json.dumps(result))
        if error is not None:
            sets.append("error=?")
            args.append(error)
        if status == JobStatus.completed.value:
            sets.append("completed_at=?")
            args.append(utcnow())
        args.append(job_id)
        with self._lock, self._conn() as c:
            c.execute(f"update jobs set {', '.join(sets)} where id=?", args)

    def get(self, job_id: str):
        with self._conn() as c:
            row = c.execute("select * from jobs where id=?", (job_id,)).fetchone()
        if not row:
            return None
        cols = ["id","status","progress","normalized_input","validation","result","error","trace_id","request_id","created_at","updated_at","completed_at"]
        d = dict(zip(cols, row))
        for k in ("normalized_input", "validation", "result"):
            d[k] = json.loads(d[k]) if d[k] else None
        return d

    def next_queued(self):
        with self._conn() as c:
            row = c.execute("select id from jobs where status=? order by created_at asc limit 1", (JobStatus.queued.value,)).fetchone()
        return row[0] if row else None
