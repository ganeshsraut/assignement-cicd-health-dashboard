import os, gzip, io
from datetime import datetime, timedelta
from .config import settings

def ensure_dir(path: str):
    os.makedirs(path, exist_ok=True)

def store_job_log_gz(owner: str, repo: str, run_id: int, job_id: int, content: bytes) -> str:
    base = settings.log_dir
    folder = os.path.join(base, f"{owner}_{repo}", str(run_id))
    ensure_dir(folder)
    path = os.path.join(folder, f"{job_id}.log.gz")
    with gzip.open(path, 'wb') as f:
        f.write(content)
    return path

def read_job_log_text(path: str, max_bytes: int = 2_000_000) -> str:
    # Read up to max_bytes after decompression
    with gzip.open(path, 'rb') as f:
        data = f.read(max_bytes)
    try:
        return data.decode('utf-8', errors='replace')
    except Exception:
        return data.decode('latin-1', errors='replace')

def cleanup_old_logs():
    if not os.path.isdir(settings.log_dir):
        return 0
    cutoff = datetime.utcnow() - timedelta(days=settings.log_retention_days)
    removed = 0
    for root, dirs, files in os.walk(settings.log_dir):
        for name in files:
            if not name.endswith('.log.gz'):
                continue
            path = os.path.join(root, name)
            try:
                mtime = datetime.utcfromtimestamp(os.path.getmtime(path))
                if mtime < cutoff:
                    os.remove(path)
                    removed += 1
            except Exception:
                pass
    return int(removed)
