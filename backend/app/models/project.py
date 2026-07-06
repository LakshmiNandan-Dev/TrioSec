from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    # Pre-filled defaults for the "new scan" form: local_path | git_url | dast_url
    default_target_type: Mapped[str | None] = mapped_column(String(32))
    default_target_value: Mapped[str | None] = mapped_column(Text)
    # Fernet-encrypted git access token, used to clone private repos for this project.
    git_token_encrypted: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    scans = relationship("Scan", back_populates="project", cascade="all, delete-orphan")

    @property
    def has_git_token(self) -> bool:
        return bool(self.git_token_encrypted)
