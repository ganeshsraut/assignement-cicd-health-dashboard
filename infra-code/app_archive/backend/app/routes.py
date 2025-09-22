from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import PlainTextResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from .database import get_db
from . import models
from .metrics import get_overview, timeseries_counts
from .logs import read_job_log_text

router = APIRouter()

@router.get("/repos")
def list_repos(db: Session = Depends(get_db)):
    repos = db.query(models.Repo).filter(models.Repo.is_active == True).order_by(models.Repo.full_name).all()
    return [{"id": r.id, "owner": r.owner, "name": r.name, "full_name": r.full_name, "default_branch": r.default_branch} for r in repos]

@router.get("/runs")
def list_runs(repo: Optional[str] = None, branch: Optional[str] = None, limit: int = 50, db: Session = Depends(get_db)):
    q = db.query(models.WorkflowRun).join(models.Repo).order_by(models.WorkflowRun.started_at.desc().nullslast())
    if repo:
        q = q.filter(models.Repo.full_name == repo)
    if branch:
        q = q.filter(models.WorkflowRun.head_branch == branch)
    runs = q.limit(limit).all()
    return [{
        "id": r.id,
        "repo": r.repo.full_name if r.repo else None,
        "workflow_name": r.workflow_name,
        "head_branch": r.head_branch,
        "event": r.event,
        "status": r.status,
        "conclusion": r.conclusion,
        "started_at": r.started_at.isoformat() if r.started_at else None,
        "completed_at": r.completed_at.isoformat() if r.completed_at else None,
        "duration_secs": r.duration_secs,
        "url": r.url,
        "actor": r.actor,
    } for r in runs]

@router.get("/runs/{run_id}/jobs")
def run_jobs(run_id: int, db: Session = Depends(get_db)):
    jobs = db.query(models.WorkflowJob).filter(models.WorkflowJob.run_id == run_id).all()
    return [{
        "id": j.id,
        "name": j.name,
        "status": j.status,
        "conclusion": j.conclusion,
        "started_at": j.started_at.isoformat() if j.started_at else None,
        "completed_at": j.completed_at.isoformat() if j.completed_at else None,
        "duration_secs": j.duration_secs,
    } for j in jobs]

@router.get("/jobs/{job_id}/log", response_class=PlainTextResponse)
def job_log(job_id: int, db: Session = Depends(get_db)):
    j = db.query(models.WorkflowJob).filter(models.WorkflowJob.id == job_id).first()
    if not j or not j.log or not j.log.path:
        raise HTTPException(status_code=404, detail="Log not found")
    text = read_job_log_text(j.log.path, max_bytes=2_000_000)
    return text

@router.get("/metrics/overview")
def overview(repo: Optional[str] = None, branch: Optional[str] = None, windowDays: int = 7, db: Session = Depends(get_db)):
    return get_overview(db, repo, branch, windowDays)

@router.get("/metrics/timeseries")
def timeseries(repo: Optional[str] = None, branch: Optional[str] = None, windowDays: int = 7, db: Session = Depends(get_db)):
    return timeseries_counts(db, repo, branch, windowDays)
