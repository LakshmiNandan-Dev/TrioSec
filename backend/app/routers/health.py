import httpx
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import get_db
from app.redis_conn import get_redis

router = APIRouter(tags=["health"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    status = {"db": False, "redis": False, "zap": False}
    try:
        db.execute(text("SELECT 1"))
        status["db"] = True
    except Exception:  # noqa: BLE001
        pass
    try:
        status["redis"] = bool(get_redis().ping())
    except Exception:  # noqa: BLE001
        pass
    try:
        r = httpx.get(
            f"{settings.zap_base_url}/JSON/core/view/version/",
            params={"apikey": settings.zap_api_key},
            timeout=3,
        )
        status["zap"] = r.status_code == 200
    except Exception:  # noqa: BLE001
        pass
    status["ok"] = all((status["db"], status["redis"], status["zap"]))
    return status
