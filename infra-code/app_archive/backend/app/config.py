import os
from pydantic import BaseModel
from typing import Optional

def _bool(s: str, default: bool=False) -> bool:
    if s is None:
        return default
    return s.lower() in ("1", "true", "yes", "y", "on")

class Settings(BaseModel):
    # GitHub
    github_token: str = os.getenv("GITHUB_TOKEN", "")
    repo_discovery_mode: str = os.getenv("REPO_DISCOVERY_MODE", "all")
    branch_filters: str = os.getenv("BRANCH_FILTERS", "")  # comma-separated
    poll_interval_seconds: int = int(os.getenv("POLL_INTERVAL_SECONDS", "30"))
    poll_shards: int = int(os.getenv("POLL_SHARDS", "4"))
    max_runs_per_repo: int = int(os.getenv("MAX_RUNS_PER_REPO", "50"))

    # Storage / Logs
    log_storage: str = os.getenv("LOG_STORAGE", "disk")
    log_dir: str = os.getenv("LOG_DIR", "/data/run-logs")
    log_gzip: bool = _bool(os.getenv("LOG_GZIP", "true"))
    log_retention_days: int = int(os.getenv("LOG_RETENTION_DAYS", "7"))
    max_log_bytes_per_job: int = int(os.getenv("MAX_LOG_BYTES_PER_JOB", "10485760"))

    # Alerts (Slack)
    alerts_enabled: bool = _bool(os.getenv("ALERTS_ENABLED", "true"))
    alert_channel_mentions: str = os.getenv("ALERT_CHANNEL_MENTIONS", "channel")  # 'channel'|'here'|''
    slack_webhook_url: str = os.getenv("SLACK_WEBHOOK_URL", "")

    # API / UI
    tz: str = os.getenv("TZ", "Asia/Kolkata")
    jwt_secret: str = os.getenv("JWT_SECRET", "change_me")
    api_port: int = int(os.getenv("API_PORT", "8080"))

    # DB
    database_url: str = os.getenv("DATABASE_URL", "postgresql://ci:ci@db:5432/ci_metrics")

settings = Settings()
