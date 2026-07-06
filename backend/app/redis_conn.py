from redis import Redis
from rq import Queue

from app.config import settings

SCAN_QUEUE = "scans"
# Generous ceiling: a full ZAP active scan of a real app can run for a long time.
SCAN_JOB_TIMEOUT = 3 * 60 * 60


def get_redis() -> Redis:
    return Redis.from_url(settings.redis_url)


def get_scan_queue(connection: Redis | None = None) -> Queue:
    return Queue(SCAN_QUEUE, connection=connection or get_redis())
