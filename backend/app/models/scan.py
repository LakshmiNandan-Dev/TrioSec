from datetime import datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

STATUS_QUEUED = "queued"
STATUS_RUNNING = "running"
STATUS_COMPLETED = "completed"
STATUS_FAILED = "failed"
STATUS_CANCELLED = "cancelled"
TERMINAL_STATUSES = {STATUS_COMPLETED, STATUS_FAILED, STATUS_CANCELLED}

SCAN_TYPES = ("sast", "sca", "dast", "iac")
# Scan types that analyze files on disk (need a resolved code path / git clone).
FILE_BASED_SCAN_TYPES = ("sast", "sca", "iac")


class Scan(Base):
    __tablename__ = "scans"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"), index=True)
    status: Mapped[str] = mapped_column(String(16), default=STATUS_QUEUED)

    # Subset of SCAN_TYPES selected for this run.
    scan_types: Mapped[list] = mapped_column(JSON, default=list)
    # local_path | git_url (code target for SAST/SCA)
    target_type: Mapped[str | None] = mapped_column(String(32))
    target_value: Mapped[str | None] = mapped_column(Text)
    dast_url: Mapped[str | None] = mapped_column(Text)
    dast_full_scan: Mapped[bool] = mapped_column(default=False)
    # Audit trail: which user confirmed they are authorized to run this DAST scan.
    authorized_by: Mapped[str | None] = mapped_column(String(255))

    job_id: Mapped[str | None] = mapped_column(String(64))
    # Per-tool sub-state, e.g. {"sast": "completed", "sca": "running"}
    tool_status: Mapped[dict] = mapped_column(JSON, default=dict)

    # Denormalized at completion; powers trends without per-finding aggregation.
    severity_counts: Mapped[dict | None] = mapped_column(JSON)
    total_findings: Mapped[int] = mapped_column(default=0)

    error_message: Mapped[str | None] = mapped_column(Text)
    logs: Mapped[str | None] = mapped_column(Text)

    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    project = relationship("Project", back_populates="scans")
    findings = relationship("Finding", back_populates="scan", cascade="all, delete-orphan")
