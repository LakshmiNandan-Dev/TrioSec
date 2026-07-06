from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.scan import TERMINAL_STATUSES, Scan
from app.models.user import User
from app.schemas.settings import EmailReportRequest
from app.services import audit_service, email_service, report_service
from app.services.audit_service import client_ip
from app.services.email_service import EmailNotConfiguredError

router = APIRouter(prefix="/reports", tags=["reports"], dependencies=[Depends(get_current_user)])


def _get_finished_scan(db: Session, scan_id: int) -> Scan:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scan not found")
    if scan.status not in TERMINAL_STATUSES:
        raise HTTPException(status.HTTP_409_CONFLICT, "Scan has not finished yet")
    return scan


@router.get("/scan/{scan_id}.json")
def report_json(scan_id: int, db: Session = Depends(get_db)):
    return report_service.report_json(db, _get_finished_scan(db, scan_id))


@router.get("/scan/{scan_id}.html")
def report_html(scan_id: int, db: Session = Depends(get_db)):
    html = report_service.render_html(db, _get_finished_scan(db, scan_id))
    return Response(content=html, media_type="text/html")


@router.get("/scan/{scan_id}.pdf")
def report_pdf(scan_id: int, db: Session = Depends(get_db)):
    pdf = report_service.render_pdf(db, _get_finished_scan(db, scan_id))
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="triosec-scan-{scan_id}.pdf"'},
    )


@router.post("/scan/{scan_id}/email")
def email_report(
    scan_id: int,
    payload: EmailReportRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    scan = _get_finished_scan(db, scan_id)
    pdf = report_service.render_pdf(db, scan)
    counts = scan.severity_counts or {}
    summary = ", ".join(f"{counts.get(sev, 0)} {sev}" for sev in ("critical", "high", "medium", "low", "info"))
    subject = f"TrioSec report — {scan.project.name} (scan #{scan.id})"
    text_body = (
        f"Security scan report for project {scan.project.name}, scan #{scan.id}.\n"
        f"Findings: {scan.total_findings} total ({summary}).\n"
        "The full report is attached as PDF."
    )
    html_body = (
        f"<p>Security scan report for project <b>{scan.project.name}</b>, scan #{scan.id}.</p>"
        f"<p>Findings: <b>{scan.total_findings}</b> total ({summary}).</p>"
        "<p>The full report is attached as PDF.</p>"
    )
    try:
        email_service.send_email(
            db,
            recipient=payload.recipient,
            subject=subject,
            text_body=text_body,
            html_body=html_body,
            pdf_attachment=(f"triosec-scan-{scan.id}.pdf", pdf),
        )
    except EmailNotConfiguredError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 — surface SMTP failures to the UI
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, f"Sending failed: {exc}") from exc
    audit_service.record(
        "report.email", actor=user, ip=client_ip(request), target=payload.recipient,
        detail={"scan_id": scan.id},
    )
    return {"sent": True, "recipient": payload.recipient}
