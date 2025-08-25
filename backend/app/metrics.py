from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from . import models

def get_overview(db: Session, repo_full: Optional[str], branch: Optional[str], window_days: int = 7) -> Dict[str, Any]:
    cutoff = datetime.utcnow() - timedelta(days=window_days)
    q = db.query(models.WorkflowRun).join(models.Repo).filter(models.WorkflowRun.started_at != None)
    q = q.filter(models.WorkflowRun.started_at >= cutoff)
    if repo_full:
        q = q.filter(models.Repo.full_name == repo_full)
    if branch:
        q = q.filter(models.WorkflowRun.head_branch == branch)

    runs = q.all()
    total = len(runs)
    successes = len([r for r in runs if r.conclusion == 'success'])
    failures = len([r for r in runs if r.conclusion == 'failure'])
    durations = [r.duration_secs for r in runs if (r.duration_secs or 0) > 0]

    avg_duration = sum(durations)/len(durations) if durations else 0.0

    # Last build (by started_at)
    last = None
    if runs:
        last = sorted(runs, key=lambda r: r.started_at or r.completed_at or datetime.min, reverse=True)[0]

    return {
        "total": total,
        "successRate": round((successes/total)*100, 2) if total else 0.0,
        "failureRate": round((failures/total)*100, 2) if total else 0.0,
        "avgDurationSecs": avg_duration,
        "lastBuild": {
            "status": last.status if last else None,
            "conclusion": last.conclusion if last else None,
            "startedAt": (last.started_at.isoformat() if last and last.started_at else None),
            "url": last.url if last else None,
            "repo": (last.repo.full_name if last and last.repo else None),
            "branch": (last.head_branch if last else None),
        }
    }

def timeseries_counts(db: Session, repo_full: Optional[str], branch: Optional[str], window_days: int = 7):
    cutoff = datetime.utcnow() - timedelta(days=window_days)
    q = db.query(models.WorkflowRun).join(models.Repo).filter(models.WorkflowRun.started_at != None)
    q = q.filter(models.WorkflowRun.started_at >= cutoff)
    if repo_full:
        q = q.filter(models.Repo.full_name == repo_full)
    if branch:
        q = q.filter(models.WorkflowRun.head_branch == branch)

    # Group by date
    buckets = {}
    for r in q.all():
        day = (r.started_at.date() if r.started_at else r.completed_at.date())
        b = buckets.setdefault(day.isoformat(), {"success":0, "failure":0, "other":0, "avgDuration":0.0, "n":0})
        if r.conclusion == 'success':
            b["success"] += 1
        elif r.conclusion == 'failure':
            b["failure"] += 1
        else:
            b["other"] += 1
        if r.duration_secs:
            b["avgDuration"] += r.duration_secs
            b["n"] += 1
    # finalize avg
    series = []
    for day in sorted(buckets.keys()):
        b = buckets[day]
        avg = (b["avgDuration"]/b["n"]) if b["n"] else 0.0
        series.append({"date": day, "success": b["success"], "failure": b["failure"], "other": b["other"], "avgDuration": avg})
    return series
