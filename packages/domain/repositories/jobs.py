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
                created_at text, updated_at text, completed_at text,
                review text, report text, idempotency_key text, artifact_version text, cancelled integer default 0
                )"""
            )
            cols = [r[1] for r in c.execute("pragma table_info(jobs)").fetchall()]
            for add in [("review","text"),("report","text"),("idempotency_key","text"),("artifact_version","text"),("cancelled","integer default 0")]:
                if add[0] not in cols:
                    c.execute(f"alter table jobs add column {add[0]} {add[1]}")

    def create(self, normalized_input: dict, validation: dict, trace_id: str, request_id: str):
        job_id = str(uuid.uuid4())
        now = utcnow()
        with self._lock, self._conn() as c:
            c.execute("insert into jobs (id,status,progress,normalized_input,validation,result,error,trace_id,request_id,created_at,updated_at,completed_at,review,report,idempotency_key,artifact_version,cancelled) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", (
                job_id, JobStatus.queued.value, 0.0, json.dumps(normalized_input), json.dumps(validation), None,
                None, trace_id, request_id, now, now, None, None, None, request_id or None, "v1", 0,
            ))
        return job_id

    def update(self, job_id: str, *, status=None, progress=None, result=None, error=None, review=None, report=None):
        sets = ["updated_at=?"]
        args = [utcnow()]
        for k,v in (("status",status),("progress",progress),("error",error)):
            if v is not None:
                sets.append(f"{k}=?")
                args.append(v)
        if result is not None:
            sets.append("result=?"); args.append(json.dumps(result))
        if review is not None:
            sets.append("review=?"); args.append(json.dumps(review))
        if report is not None:
            sets.append("report=?"); args.append(json.dumps(report))
        if status in {JobStatus.completed.value, JobStatus.approved.value, JobStatus.rejected.value}:
            sets.append("completed_at=?"); args.append(utcnow())
        args.append(job_id)
        with self._lock, self._conn() as c:
            c.execute(f"update jobs set {', '.join(sets)} where id=?", args)

    def get(self, job_id: str):
        with self._conn() as c:
            row = c.execute("select * from jobs where id=?", (job_id,)).fetchone()
        if not row:
            return None
        cols = ["id","status","progress","normalized_input","validation","result","error","trace_id","request_id","created_at","updated_at","completed_at","review","report","idempotency_key","artifact_version","cancelled"]
        d = dict(zip(cols, row))
        for k in ("normalized_input", "validation", "result", "review", "report"):
            d[k] = json.loads(d[k]) if d[k] else None
        return d

    def next_queued(self):
        with self._conn() as c:
            row = c.execute("select id from jobs where status=? order by created_at asc limit 1", (JobStatus.queued.value,)).fetchone()
        return row[0] if row else None


    def find_by_idempotency_key(self, key: str):
        if not key:
            return None
        with self._conn() as c:
            row = c.execute("select id from jobs where idempotency_key=? order by created_at desc limit 1", (key,)).fetchone()
        return self.get(row[0]) if row else None
