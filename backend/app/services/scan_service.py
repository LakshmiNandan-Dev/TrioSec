from datetime import datetime, timezone

from rq.command import send_stop_job_command
from rq.job import Job
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.app_setting import AppSetting
from app.models.finding import SEVERITY_RANK, Finding
from app.models.scan import (
    FILE_BASED_SCAN_TYPES,
    SCAN_TYPES,
    STATUS_CANCELLED,
    STATUS_COMPLETED,
    STATUS_QUEUED,
    STATUS_RUNNING,
    Scan,
)
from app.redis_conn import SCAN_JOB_TIMEOUT, get_redis, get_scan_queue
from app.schemas.scan import ScanCreate, TrendPoint
from app.services import path_service
from app.services.path_service import TargetValidationError


def validate_scan_request(payload: ScanCreate, allowed_dast_domains: list[str] | None = None) -> list[str]:
    types = [t for t in SCAN_TYPES if t in payload.scan_types]
    if not types:
        raise TargetValidationError("Select at least one scan type (sast, sca, dast, iac)")
    if any(t in types for t in FILE_BASED_SCAN_TYPES):
        if payload.target_type == "local_path":
            path_service.resolve_workspace_path(payload.target_value or "")
        elif payload.target_type == "git_url":
            path_service.validate_git_url(payload.target_value or "")
        else:
            raise TargetValidationError(
                "target_type must be local_path or git_url for code/IaC scans"
            )
    if "dast" in types:
        url = path_service.validate_dast_url(payload.dast_url or "")
        if not payload.authorization_acknowledged:
            raise TargetValidationError(
                "You must confirm you own or are authorized to test this target before "
                "starting a DAST scan"
            )
        if allowed_dast_domains and not path_service.dast_host_allowed(url, allowed_dast_domains):
            raise TargetValidationError(
                "This target host is not in the approved DAST allowlist. "
                f"Approved domains: {', '.join(allowed_dast_domains)}"
            )
    return types


def create_scan(db: Session, payload: ScanCreate, authorized_by: str | None = None) -> Scan:
    cfg = db.get(AppSetting, 1)
    allowed = path_service.parse_domain_list(cfg.dast_allowed_domains if cfg else None)
    types = validate_scan_request(payload, allowed_dast_domains=allowed)
    scan = Scan(
        project_id=payload.project_id,
        status=STATUS_QUEUED,
        scan_types=types,
        target_type=payload.target_type,
        target_value=payload.target_value,
        dast_url=payload.dast_url,
        dast_full_scan=payload.dast_full_scan,
        authorized_by=authorized_by if "dast" in types else None,
        tool_status={t: STATUS_QUEUED for t in types},
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    job = get_scan_queue().enqueue("app.worker.tasks.run_scan", scan.id, job_timeout=SCAN_JOB_TIMEOUT)
    scan.job_id = job.id
    db.commit()
    return scan


def cancel_scan(db: Session, scan: Scan) -> Scan:
    if scan.status not in (STATUS_QUEUED, STATUS_RUNNING):
        raise ValueError(f"Scan is already {scan.status}")
    if scan.job_id:
        conn = get_redis()
        try:
            if scan.status == STATUS_QUEUED:
                Job.fetch(scan.job_id, connection=conn).cancel()
            else:
                send_stop_job_command(conn, scan.job_id)
        except Exception:  # noqa: BLE001 — job may have just finished or never registered
            pass
    scan.status = STATUS_CANCELLED
    scan.finished_at = datetime.now(timezone.utc)
    scan.tool_status = {
        t: (s if s in (STATUS_COMPLETED, "failed") else STATUS_CANCELLED)
        for t, s in (scan.tool_status or {}).items()
    }
    db.commit()
    return scan


def project_trends(db: Session, project_id: int) -> list[TrendPoint]:
    scans = db.scalars(
        select(Scan)
        .where(Scan.project_id == project_id, Scan.status == STATUS_COMPLETED)
        .order_by(Scan.finished_at)
    ).all()
    points = []
    for s in scans:
        counts = s.severity_counts or {}
        points.append(
            TrendPoint(
                scan_id=s.id,
                finished_at=s.finished_at,
                total=s.total_findings,
                **{sev: counts.get(sev, 0) for sev in ("critical", "high", "medium", "low", "info")},
            )
        )
    return points


def compare_scans(db: Session, base_id: int, head_id: int) -> tuple[list[Finding], list[Finding], int]:
    def fp_map(scan_id: int) -> dict[str, Finding]:
        return {f.fingerprint: f for f in db.scalars(select(Finding).where(Finding.scan_id == scan_id))}

    base, head = fp_map(base_id), fp_map(head_id)
    by_severity = lambda f: -SEVERITY_RANK.get(f.severity, 0)  # noqa: E731
    added = sorted((head[fp] for fp in head.keys() - base.keys()), key=by_severity)
    fixed = sorted((base[fp] for fp in base.keys() - head.keys()), key=by_severity)
    return added, fixed, len(base.keys() & head.keys())
