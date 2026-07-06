from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.deps import get_current_admin, get_db
from app.models.app_setting import AppSetting
from app.models.user import User
from app.schemas.settings import SettingsOut, SettingsUpdate, SmtpTestRequest
from app.services import audit_service, email_service
from app.services.audit_service import client_ip
from app.services.crypto import encrypt_str
from app.services.email_service import EmailNotConfiguredError

# Settings (SMTP, DAST allowlist) are admin-only.
router = APIRouter(prefix="/settings", tags=["settings"], dependencies=[Depends(get_current_admin)])


def _get_settings_row(db: Session) -> AppSetting:
    row = db.get(AppSetting, 1)
    if row is None:
        row = AppSetting(id=1)
        db.add(row)
        db.commit()
        db.refresh(row)
    return row


def _to_out(row: AppSetting) -> SettingsOut:
    return SettingsOut(
        smtp_host=row.smtp_host,
        smtp_port=row.smtp_port,
        smtp_username=row.smtp_username,
        smtp_use_tls=row.smtp_use_tls,
        smtp_from_address=row.smtp_from_address,
        default_semgrep_config=row.default_semgrep_config,
        dast_allowed_domains=row.dast_allowed_domains,
        has_smtp_password=bool(row.smtp_password_encrypted),
    )


@router.get("", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db)):
    return _to_out(_get_settings_row(db))


@router.put("", response_model=SettingsOut)
def update_settings(
    payload: SettingsUpdate,
    request: Request,
    current: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    row = _get_settings_row(db)
    data = payload.model_dump(exclude_unset=True)
    password = data.pop("smtp_password", None)
    for key, value in data.items():
        setattr(row, key, value)
    if password:  # only overwrite when a non-empty value is supplied
        row.smtp_password_encrypted = encrypt_str(password)
    db.commit()
    db.refresh(row)
    # Record which fields changed (never the values — some are secrets).
    changed = sorted(data.keys()) + (["smtp_password"] if password else [])
    audit_service.record(
        "settings.update", actor=current, ip=client_ip(request), detail={"changed": changed}
    )
    return _to_out(row)


@router.post("/smtp/test")
def test_smtp(payload: SmtpTestRequest, db: Session = Depends(get_db)):
    try:
        email_service.send_email(
            db,
            recipient=payload.recipient,
            subject="TrioSec SMTP test",
            text_body="This is a test email from TrioSec. Your SMTP settings work.",
        )
    except EmailNotConfiguredError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"SMTP test failed: {exc}") from exc
    return {"sent": True, "recipient": payload.recipient}
