from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta, timezone
from dateutil import parser as dtparser
from typing import List, Dict, Tuple
import time

from .config import settings
from .database import SessionLocal
from .github import GitHubClient
from . import models
from .logs import store_job_log_gz, cleanup_old_logs, read_job_log_text
from .slack import post_slack_webhook, render_failure_blocks

scheduler = BackgroundScheduler()
client = None
shard_index = 0

def start_scheduler():
    global client
    client = GitHubClient(settings.github_token)
    # Run repo discovery on startup
    discover_and_sync_repos()
    # Start jobs
    scheduler.add_job(poll_tick, "interval", seconds=settings.poll_interval_seconds, id="poll")
    scheduler.add_job(retention_tick, "cron", hour="*/6", id="retention")  # cleanup every 6 hours
    scheduler.start()

def discover_and_sync_repos():
    db: Session = SessionLocal()
    try:
        repos = client.list_all_repos()
        existing = {r.full_name: r for r in db.query(models.Repo).all()}
        for r in repos:
            full = r.get("full_name")
            owner = r.get("owner", {}).get("login")
            name = r.get("name")
            default_branch = r.get("default_branch")
            if full in existing:
                item = existing[full]
                item.default_branch = default_branch
                item.is_active = True
            else:
                db.add(models.Repo(
                    owner=owner,
                    name=name,
                    full_name=full,
                    default_branch=default_branch,
                    is_active=True
                ))
        # Optionally deactivate repos no longer visible (keep them active for simplicity)
        db.commit()
    finally:
        db.close()

def select_repos_for_tick(db: Session) -> List[models.Repo]:
    # shard repos across ticks
    global shard_index
    repos = db.query(models.Repo).filter(models.Repo.is_active == True).order_by(models.Repo.id).all()
    n = len(repos) or 1
    shards = settings.poll_shards if settings.poll_shards > 0 else 1
    per = max(1, n // shards)
    start = (shard_index * per) % n
    end = start + per
    shard_index = (shard_index + 1) % shards
    return repos[start:end]

def poll_tick():
    db: Session = SessionLocal()
    try:
        repos = select_repos_for_tick(db)
        for r in repos:
            try:
                ingest_repo_runs(db, r)
                db.commit()
            except Exception as e:
                db.rollback()
                # you may want to log this to a file
    finally:
        db.close()

def parse_time(s: str):
    if not s:
        return None
    return dtparser.parse(s)

def ingest_repo_runs(db: Session, repo: models.Repo):
    data = client.list_runs(repo.owner, repo.name, per_page=settings.max_runs_per_repo)
    runs = data.get("workflow_runs", [])
    branch_filters = [b.strip() for b in settings.branch_filters.split(",") if b.strip()] if settings.branch_filters else []

    for run in runs:
        run_id = run.get("id")
        head_branch = run.get("head_branch")
        if branch_filters and head_branch not in branch_filters:
            continue

        existing = db.get(models.WorkflowRun, run_id)
        started_at = parse_time(run.get("run_started_at") or run.get("created_at"))
        completed_at = parse_time(run.get("updated_at") if run.get("status") != "completed" else run.get("updated_at"))
        # GitHub returns 'updated_at' even while in progress; we compute duration only if completed and have started_at
        duration = None
        if started_at and run.get("status") == "completed" and run.get("updated_at"):
            end = parse_time(run.get("updated_at"))
            duration = (end - started_at).total_seconds()

        if not existing:
            rec = models.WorkflowRun(
                id=run_id,
                repo_id=repo.id,
                workflow_name=run.get("name"),
                head_branch=head_branch,
                head_sha=run.get("head_sha"),
                event=run.get("event"),
                status=run.get("status"),
                conclusion=run.get("conclusion"),
                started_at=started_at,
                completed_at=parse_time(run.get("updated_at")) if run.get("status") == "completed" else None,
                duration_secs=duration,
                url=run.get("html_url"),
                actor=(run.get("actor") or {}).get("login") if run.get("actor") else None,
            )
            db.add(rec)
            db.flush()  # ensure inserted for FK
            # If failed, fetch jobs + logs and alert
            if rec.conclusion == "failure":
                ingest_jobs_and_logs(db, repo, rec)
                send_failure_alert(repo, rec, db)
        else:
            # Update mutable fields
            existing.status = run.get("status")
            existing.conclusion = run.get("conclusion")
            existing.started_at = started_at
            existing.completed_at = parse_time(run.get("updated_at")) if run.get("status") == "completed" else None
            existing.duration_secs = duration
            existing.url = run.get("html_url")
            db.add(existing)
            db.flush()
            if existing.conclusion == "failure":
                # ensure jobs/logs exist
                has_jobs = db.query(models.WorkflowJob).filter(models.WorkflowJob.run_id == existing.id).first()
                if not has_jobs:
                    ingest_jobs_and_logs(db, repo, existing)
                    send_failure_alert(repo, existing, db)

    repo.last_checked_at = datetime.utcnow()
    db.add(repo)

def ingest_jobs_and_logs(db: Session, repo: models.Repo, run: models.WorkflowRun):
    jobs = client.list_jobs_for_run(repo.owner, repo.name, run.id).get("jobs", [])
    for j in jobs:
        job_id = j.get("id")
        started_at = parse_time(j.get("started_at"))
        completed_at = parse_time(j.get("completed_at"))
        duration = (completed_at - started_at).total_seconds() if started_at and completed_at else None
        job_rec = models.WorkflowJob(
            id=job_id,
            run_id=run.id,
            name=j.get("name"),
            status=j.get("status"),
            conclusion=j.get("conclusion"),
            started_at=started_at,
            completed_at=completed_at,
            duration_secs=duration,
        )
        db.merge(job_rec)  # merge to upsert
        db.flush()

        # Steps
        for s in j.get("steps", []) or []:
            step = models.WorkflowStep(
                job_id=job_id,
                name=s.get("name"),
                status=s.get("status"),
                conclusion=s.get("conclusion"),
                number=s.get("number"),
                started_at=parse_time(s.get("started_at")),
                completed_at=parse_time(s.get("completed_at")),
            )
            db.add(step)

        # Logs only for failed jobs (respect size cap)
        if j.get("conclusion") == "failure":
            try:
                data = client.download_job_log(repo.owner, repo.name, job_id)
                if len(data) <= settings.max_log_bytes_per_job:
                    path = store_job_log_gz(repo.owner, repo.name, run.id, job_id, data)
                    log = models.RunLog(job_id=job_id, storage="disk", path=path, size_bytes=len(data))
                    db.merge(log)
            except Exception:
                pass

def summarize_failed_jobs(db: Session, run_id: int) -> str:
    # Return a small human-readable summary for alert
    jobs = db.query(models.WorkflowJob).filter(models.WorkflowJob.run_id == run_id).all()
    failed = [j for j in jobs if j.conclusion == "failure"]
    if not failed:
        return "No failed jobs details available."
    parts = [f"• {j.name} (id {j.id})" for j in failed]
    return "\n".join(parts[:10])

def get_log_snippet(db: Session, run_id: int, lines: int = 200) -> str:
    jobs = db.query(models.WorkflowJob).filter(models.WorkflowJob.run_id == run_id).all()
    for j in jobs:
        if j.conclusion == "failure" and j.log and j.log.path:
            txt = read_job_log_text(j.log.path, max_bytes=1_000_000)
            if not txt:
                continue
            # get last N lines
            arr = txt.splitlines()
            return "\n".join(arr[-lines:])
    return ""

def send_failure_alert(repo: models.Repo, run: models.WorkflowRun, db: Session):
    if not settings.alerts_enabled or not settings.slack_webhook_url:
        return
    mention = settings.alert_channel_mentions.strip()
    prefix = settings.alert_title_prefix if hasattr(settings, 'alert_title_prefix') else "[CI Failure]"
    # Duration to friendly
    dur = f"{int((run.duration_secs or 0)//60)}m {(int(run.duration_secs or 0)%60)}s"
    snippet = get_log_snippet(db, run.id, lines=int(getattr(settings, 'alert_log_snippet_lines', 200)))
    blocks = render_failure_blocks(prefix, mention, repo.full_name, run.head_branch or "-", run.workflow_name or "-", run.conclusion or "-", dur, run.url or "-", snippet if getattr(settings, 'alert_include_log_snippet', True) else "")
    text = f"{prefix} {repo.full_name} {run.workflow_name} failed"
    post_slack_webhook(settings.slack_webhook_url, text, blocks=blocks)

def retention_tick():
    cleanup_old_logs()
