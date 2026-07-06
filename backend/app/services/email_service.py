import smtplib
import ssl
from email.message import EmailMessage

from sqlalchemy.orm import Session

from app.models.app_setting import AppSetting
from app.services.crypto import decrypt_str


class EmailNotConfiguredError(ValueError):
    pass


def _get_config(db: Session) -> AppSetting:
    cfg = db.get(AppSetting, 1)
    if cfg is None or not cfg.smtp_host or not cfg.smtp_from_address:
        raise EmailNotConfiguredError("SMTP is not configured — set host and from-address under Settings")
    return cfg


def send_email(
    db: Session,
    recipient: str,
    subject: str,
    text_body: str,
    html_body: str | None = None,
    pdf_attachment: tuple[str, bytes] | None = None,
) -> None:
    cfg = _get_config(db)

    msg = EmailMessage()
    msg["From"] = cfg.smtp_from_address
    msg["To"] = recipient
    msg["Subject"] = subject
    msg.set_content(text_body)
    if html_body:
        msg.add_alternative(html_body, subtype="html")
    if pdf_attachment:
        filename, data = pdf_attachment
        msg.add_attachment(data, maintype="application", subtype="pdf", filename=filename)

    with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port, timeout=30) as smtp:
        if cfg.smtp_use_tls:
            smtp.starttls(context=ssl.create_default_context())
        if cfg.smtp_username and cfg.smtp_password_encrypted:
            smtp.login(cfg.smtp_username, decrypt_str(cfg.smtp_password_encrypted))
        smtp.send_message(msg)
