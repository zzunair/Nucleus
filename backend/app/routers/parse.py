from arq.connections import ArqRedis
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import ParseJob
from app.schemas import ParseJobOut, ParseRequest

router = APIRouter(prefix="/parse", tags=["AI parse"])


@router.post("", response_model=ParseJobOut, status_code=202)
async def submit(body: ParseRequest, request: Request, db: Session = Depends(get_db)):
    """Queue raw text for AI parsing; poll GET /parse/{id} for the result."""
    job = ParseJob(input_text=body.text, source=body.source)
    db.add(job)
    db.commit()
    redis: ArqRedis = request.app.state.redis
    await redis.enqueue_job("parse_job", job.id)
    return job


@router.get("/{job_id}", response_model=ParseJobOut)
def status(job_id: int, db: Session = Depends(get_db)):
    job = db.get(ParseJob, job_id)
    if not job:
        raise HTTPException(404, "job not found")
    return job
