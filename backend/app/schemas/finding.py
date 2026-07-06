from pydantic import BaseModel, ConfigDict


class FindingBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    tool: str
    category: str
    severity: str
    title: str
    file_path: str | None
    url: str | None
    package_name: str | None


class FindingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    scan_id: int
    tool: str
    category: str
    severity: str
    title: str
    description: str | None
    rule_id: str | None
    cwe: str | None
    cve: str | None
    file_path: str | None
    line_start: int | None
    line_end: int | None
    url: str | None
    package_name: str | None
    installed_version: str | None
    fixed_version: str | None
    fingerprint: str
    is_new: bool
    remediation: str | None
    raw: dict | None


class FindingPage(BaseModel):
    items: list[FindingOut]
    total: int
    page: int
    page_size: int
