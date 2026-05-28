import json
import os
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
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
            c.execute(
                """create table if not exists feedback (
                id integer primary key autoincrement,
                job_id text not null,
                reviewer_id text,
                source_id text,
                context_tag text,
                observed_at text,
                rating integer,
                achieved_motion integer,
                achieved_force integer,
                achieved_pressure integer,
                notes text,
                created_at text,
                foreign key(job_id) references jobs(id)
                )"""
            )
            feedback_cols = [r[1] for r in c.execute("pragma table_info(feedback)").fetchall()]
            for add in [("reviewer_id", "text"), ("source_id", "text"), ("context_tag", "text"), ("observed_at", "text")]:
                if add[0] not in feedback_cols:
                    c.execute(f"alter table feedback add column {add[0]} {add[1]}")
            c.execute(
                "create unique index if not exists uq_feedback_job_reviewer on feedback(job_id, reviewer_id) where reviewer_id is not null"
            )
            c.execute(
                "create unique index if not exists uq_feedback_job_source on feedback(job_id, source_id) where reviewer_id is null and source_id is not null"
            )

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

    def add_feedback(self, job_id: str, payload: dict):
        reviewer_id = payload.get("reviewer_id")
        source_id = payload.get("source_id")
        if not reviewer_id and not source_id:
            raise ValueError("either reviewer_id or source_id is required")
        with self._lock, self._conn() as c:
            c.execute(
                "insert into feedback (job_id,reviewer_id,source_id,context_tag,observed_at,rating,achieved_motion,achieved_force,achieved_pressure,notes,created_at) values (?,?,?,?,?,?,?,?,?,?,?)",
                (
                    job_id,
                    reviewer_id,
                    source_id,
                    payload.get("context_tag"),
                    payload.get("observed_at"),
                    payload.get("rating"),
                    1 if payload.get("achieved_motion") else 0,
                    1 if payload.get("achieved_force") else 0,
                    1 if payload.get("achieved_pressure") else 0,
                    payload.get("notes"),
                    utcnow(),
                ),
            )

    def feedback_window_days(self) -> int:
        return int(os.getenv("FEEDBACK_WINDOW_DAYS", "30"))

    def is_feedback_window_open(self, job: dict) -> bool:
        completed_at = job.get("completed_at")
        if not completed_at:
            return False
        completed = datetime.fromisoformat(completed_at)
        return datetime.now(timezone.utc) <= completed + timedelta(days=self.feedback_window_days())

    def feedback_summary(self):
        with self._conn() as c:
            row = c.execute(
                """select count(*), avg(rating),
                avg(achieved_motion), avg(achieved_force), avg(achieved_pressure)
                from feedback"""
            ).fetchone()
        total, avg_rating, motion, force, pressure = row
        return {
            "total_feedback": total or 0,
            "avg_rating": float(avg_rating or 0.0),
            "success_rates": {
                "motion": float(motion or 0.0),
                "force": float(force or 0.0),
                "pressure": float(pressure or 0.0),
            },
        }
