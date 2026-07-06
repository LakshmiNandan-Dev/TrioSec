from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.deps import get_current_admin, get_db
from app.models.audit_event import AuditEvent
from app.schemas.audit import AuditEventOut, AuditPage

router = APIRouter(prefix="/audit", tags=["audit"], dependencies=[Depends(get_current_admin)])


@router.get("", response_model=AuditPage)
def list_audit(
    action: str | None = None,
    actor: str | None = None,
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    filters = []
    if action:
        filters.append(AuditEvent.action == action)
    if actor:
        filters.append(AuditEvent.actor_email.ilike(f"%{actor}%"))
    if q:
        like = f"%{q}%"
        filters.append(
            or_(
                AuditEvent.action.ilike(like),
                AuditEvent.actor_email.ilike(like),
                AuditEvent.target.ilike(like),
                AuditEvent.ip.ilike(like),
            )
        )

    total = db.scalar(select(func.count()).select_from(AuditEvent).where(*filters)) or 0
    items = db.scalars(
        select(AuditEvent)
        .where(*filters)
        .order_by(AuditEvent.created_at.desc(), AuditEvent.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return AuditPage(
        items=[AuditEventOut.model_validate(e) for e in items],
        total=total,
        page=page,
        page_size=page_size,
    )
