from fastapi import Request

from app.db import SessionLocal
from app.models.audit_event import AuditEvent
from app.models.user import User


def client_ip(request: Request | None) -> str | None:
    """Real client IP. nginx forwards it via X-Forwarded-For / X-Real-IP (the raw
    socket peer is only the proxy)."""
    if request is None:
        return None
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    xri = request.headers.get("x-real-ip")
    if xri:
        return xri.strip()
    return request.client.host if request.client else None


def record(
    action: str,
    *,
    actor: User | None = None,
    ip: str | None = None,
    target: str | None = None,
    detail: dict | None = None,
) -> None:
    """Append one audit event. Uses its own session so the write survives even when
    the surrounding request fails (e.g. a rejected login)."""
    try:
        with SessionLocal() as db:
            db.add(
                AuditEvent(
                    action=action,
                    actor_email=actor.email if actor else None,
                    actor_id=actor.id if actor else None,
                    ip=ip,
                    target=(target or None) and str(target)[:2000],
                    detail=detail,
                )
            )
            db.commit()
    except Exception as exc:  # noqa: BLE001 — auditing must never break the request
        print(f"audit: failed to record {action}: {exc}", flush=True)
