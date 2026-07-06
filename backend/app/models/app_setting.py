from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class AppSetting(Base):
    """Singleton row (id=1) holding runtime-configurable settings."""

    __tablename__ = "app_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    smtp_host: Mapped[str | None] = mapped_column(String(255))
    smtp_port: Mapped[int] = mapped_column(Integer, default=587)
    smtp_username: Mapped[str | None] = mapped_column(String(255))
    smtp_password_encrypted: Mapped[str | None] = mapped_column(Text)
    smtp_use_tls: Mapped[bool] = mapped_column(default=True)
    smtp_from_address: Mapped[str | None] = mapped_column(String(255))
    default_semgrep_config: Mapped[str] = mapped_column(String(255), default="p/default")
    # Approved DAST target hosts (whitespace/comma separated). Empty = no allowlist.
    dast_allowed_domains: Mapped[str | None] = mapped_column(Text)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())
