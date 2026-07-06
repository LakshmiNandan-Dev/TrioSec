from sqlalchemy import JSON, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

SEVERITIES = ("critical", "high", "medium", "low", "info")
SEVERITY_RANK = {sev: rank for rank, sev in enumerate(reversed(SEVERITIES))}


class Finding(Base):
    __tablename__ = "findings"
    __table_args__ = (
        Index("ix_findings_scan_severity", "scan_id", "severity"),
        Index("ix_findings_scan_tool", "scan_id", "tool"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    scan_id: Mapped[int] = mapped_column(ForeignKey("scans.id", ondelete="CASCADE"), index=True)

    tool: Mapped[str] = mapped_column(String(16))  # semgrep | trivy | zap
    category: Mapped[str] = mapped_column(String(16))  # sast | sca | secret | dast
    severity: Mapped[str] = mapped_column(String(16))  # critical..info

    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)
    rule_id: Mapped[str | None] = mapped_column(String(255))
    cwe: Mapped[str | None] = mapped_column(String(32))
    cve: Mapped[str | None] = mapped_column(String(64))

    file_path: Mapped[str | None] = mapped_column(Text)
    line_start: Mapped[int | None] = mapped_column(Integer)
    line_end: Mapped[int | None] = mapped_column(Integer)
    url: Mapped[str | None] = mapped_column(Text)
    package_name: Mapped[str | None] = mapped_column(String(255))
    installed_version: Mapped[str | None] = mapped_column(String(128))
    fixed_version: Mapped[str | None] = mapped_column(String(128))

    fingerprint: Mapped[str] = mapped_column(String(64), index=True)
    is_new: Mapped[bool] = mapped_column(default=False)
    remediation: Mapped[str | None] = mapped_column(Text)
    raw: Mapped[dict | None] = mapped_column(JSON)

    scan = relationship("Scan", back_populates="findings")
