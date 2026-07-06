from pydantic import BaseModel


class SettingsOut(BaseModel):
    smtp_host: str | None
    smtp_port: int
    smtp_username: str | None
    smtp_use_tls: bool
    smtp_from_address: str | None
    default_semgrep_config: str
    dast_allowed_domains: str | None
    has_smtp_password: bool


class SettingsUpdate(BaseModel):
    smtp_host: str | None = None
    smtp_port: int | None = None
    smtp_username: str | None = None
    # Write-only: stored encrypted; only overwritten when non-empty.
    smtp_password: str | None = None
    smtp_use_tls: bool | None = None
    smtp_from_address: str | None = None
    default_semgrep_config: str | None = None
    dast_allowed_domains: str | None = None


class SmtpTestRequest(BaseModel):
    recipient: str


class EmailReportRequest(BaseModel):
    recipient: str
