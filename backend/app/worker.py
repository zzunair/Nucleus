"""arq worker. Run from backend/:  python -m arq app.worker.WorkerSettings"""
from arq.connections import RedisSettings

from app.ai import call_ollama, save_parsed
from app.config import REDIS_URL
from app.database import SessionLocal
from app.models import ParseJob


async def parse_job(ctx, job_id: int):
    with SessionLocal() as db:
        job = db.get(ParseJob, job_id)
        if job is None:
            return
        job.status = "running"
        db.commit()
        try:
            parsed = await call_ollama(job.input_text)
            job.result = save_parsed(db, parsed)
            job.status = "done"
        except Exception as e:  # record the failure on the job instead of losing it
            db.rollback()
            job = db.get(ParseJob, job_id)
            job.status, job.error = "failed", f"{type(e).__name__}: {e}"
        db.commit()


class WorkerSettings:
    functions = [parse_job]
    redis_settings = RedisSettings.from_dsn(REDIS_URL)
    max_tries = 1  # an LLM failure won't fix itself on retry; inspect the job instead
    job_timeout = 600
    max_jobs = 1  # one local model; don't run parses concurrently
