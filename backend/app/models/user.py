from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    # Null for accounts provisioned via SSO — they have no local password.
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # Role: admin (manage users + settings + scans) vs member (scans only).
    is_admin: Mapped[bool] = mapped_column(default=True)
    # Deactivated accounts keep their audit trail but cannot log in.
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
