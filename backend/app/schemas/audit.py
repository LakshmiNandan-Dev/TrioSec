from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    action: str
    actor_email: str | None
    target: str | None
    ip: str | None
    detail: dict | None


class AuditPage(BaseModel):
    items: list[AuditEventOut]
    total: int
    page: int
    page_size: int
