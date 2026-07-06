from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    description: str | None = None
    default_target_type: str | None = None
    default_target_value: str | None = None
    # Write-only: stored encrypted for cloning private repos.
    git_token: str | None = None


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
    default_target_type: str | None = None
    default_target_value: str | None = None
    # Write-only; only overwritten when non-empty. Use clear_git_token to remove it.
    git_token: str | None = None
    clear_git_token: bool = False


class ProjectOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None
    default_target_type: str | None
    default_target_value: str | None
    has_git_token: bool
    created_at: datetime
