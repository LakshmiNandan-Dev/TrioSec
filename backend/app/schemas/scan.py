from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.finding import FindingBrief


class ScanCreate(BaseModel):
    project_id: int
    scan_types: list[str]
    target_type: str | None = None  # local_path | git_url
    target_value: str | None = None
    dast_url: str | None = None
    dast_full_scan: bool = False
    # Required for DAST: caller confirms they own or are authorized to test the target.
    authorization_acknowledged: bool = False


class ScanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    project_id: int
    status: str
    scan_types: list[str]
    target_type: str | None
    target_value: str | None
    dast_url: str | None
    dast_full_scan: bool
    authorized_by: str | None
    tool_status: dict
    severity_counts: dict | None
    total_findings: int
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime


class TrendPoint(BaseModel):
    scan_id: int
    finished_at: datetime | None
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    info: int = 0
    total: int = 0


class CompareResult(BaseModel):
    base_scan_id: int
    head_scan_id: int
    added: list[FindingBrief]
    fixed: list[FindingBrief]
    unchanged_count: int
