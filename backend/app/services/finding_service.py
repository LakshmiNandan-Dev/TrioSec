import hashlib
from urllib.parse import urlsplit

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.finding import SEVERITIES, SEVERITY_RANK, Finding
from app.models.scan import STATUS_COMPLETED, Scan
from app.scanners.base import RawFinding


def normalize_url(url: str | None) -> str:
    if not url:
        return ""
    parts = urlsplit(url)
    return f"{parts.scheme}://{parts.netloc}{parts.path}".lower()


def compute_fingerprint(rf: RawFinding) -> str:
    if rf.tool == "semgrep":
        parts = ("semgrep", rf.rule_id, rf.file_path, rf.line_start)
    elif rf.tool == "trivy" and rf.category == "secret":
        parts = ("trivy-secret", rf.rule_id, rf.file_path, rf.line_start)
    elif rf.tool == "trivy" and rf.category == "iac":
        parts = ("trivy-iac", rf.rule_id, rf.file_path, rf.line_start)
    elif rf.tool == "trivy":
        parts = ("trivy", rf.cve, rf.package_name, rf.installed_version)
    else:  # zap
        param = (rf.raw or {}).get("param", "")
        parts = ("zap", rf.rule_id, rf.title, normalize_url(rf.url), param)
    joined = "|".join(str(p or "").strip().lower() for p in parts)
    return hashlib.sha256(joined.encode()).hexdigest()


def dedup(raw_findings: list[RawFinding]) -> dict[str, RawFinding]:
    """Collapse duplicate fingerprints, keeping the highest severity instance."""
    by_fp: dict[str, RawFinding] = {}
    for rf in raw_findings:
        if rf.severity not in SEVERITIES:
            rf.severity = "info"
        fp = compute_fingerprint(rf)
        existing = by_fp.get(fp)
        if existing is None or SEVERITY_RANK[rf.severity] > SEVERITY_RANK[existing.severity]:
            by_fp[fp] = rf
    return by_fp


def previous_fingerprints(db: Session, scan: Scan) -> set[str]:
    prev_id = db.scalar(
        select(Scan.id)
        .where(
            Scan.project_id == scan.project_id,
            Scan.status == STATUS_COMPLETED,
            Scan.id != scan.id,
            Scan.created_at < scan.created_at,
        )
        .order_by(Scan.created_at.desc())
        .limit(1)
    )
    if prev_id is None:
        return set()
    return set(db.scalars(select(Finding.fingerprint).where(Finding.scan_id == prev_id)))


def persist_findings(db: Session, scan: Scan, raw_findings: list[RawFinding]) -> tuple[dict, int]:
    deduped = dedup(raw_findings)
    prev_fps = previous_fingerprints(db, scan)

    counts = {sev: 0 for sev in SEVERITIES}
    for fp, rf in deduped.items():
        counts[rf.severity] += 1
        db.add(
            Finding(
                scan_id=scan.id,
                tool=rf.tool,
                category=rf.category,
                severity=rf.severity,
                title=rf.title[:1000],
                description=rf.description,
                rule_id=rf.rule_id,
                cwe=rf.cwe,
                cve=rf.cve,
                file_path=rf.file_path,
                line_start=rf.line_start,
                line_end=rf.line_end,
                url=rf.url,
                package_name=rf.package_name,
                installed_version=rf.installed_version,
                fixed_version=rf.fixed_version,
                fingerprint=fp,
                is_new=bool(prev_fps) and fp not in prev_fps,
                remediation=rf.remediation,
                raw=rf.raw,
            )
        )
    return counts, len(deduped)
