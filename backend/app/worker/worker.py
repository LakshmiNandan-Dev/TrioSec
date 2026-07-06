"""RQ worker entrypoint: python -m app.worker.worker"""
import subprocess

from redis import Redis
from rq import Queue, Worker

from app.config import settings
from app.redis_conn import SCAN_QUEUE


def warm_trivy_cache() -> None:
    """Pre-download the Trivy vulnerability DB so the first scan isn't slow."""
    try:
        print("warming trivy vulnerability DB (first run may take a few minutes)…", flush=True)
        subprocess.run(["trivy", "image", "--download-db-only", "--quiet"], timeout=900, check=False)
    except Exception as exc:  # noqa: BLE001 — non-fatal; scans will retry the download
        print(f"trivy DB warm-up skipped: {exc}", flush=True)


def main() -> None:
    settings.validate_secrets()
    warm_trivy_cache()
    connection = Redis.from_url(settings.redis_url)
    worker = Worker([Queue(SCAN_QUEUE, connection=connection)], connection=connection)
    worker.work()


if __name__ == "__main__":
    main()
