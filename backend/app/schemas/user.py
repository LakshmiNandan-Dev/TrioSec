from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8)
    is_admin: bool = False


class UserUpdate(BaseModel):
    is_admin: bool | None = None
    is_active: bool | None = None
    # Admin password reset; only applied when non-empty.
    password: str | None = Field(default=None, min_length=8)
