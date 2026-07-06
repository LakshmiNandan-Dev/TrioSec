from datetime import datetime, timezone
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.finding import SEVERITIES, SEVERITY_RANK, Finding
from app.models.scan import Scan
from app.schemas.finding import FindingOut
from app.schemas.scan import ScanOut

_env = Environment(
    loader=FileSystemLoader(Path(__file__).resolve().parents[1] / "templates"),
    autoescape=select_autoescape(["html"]),
)


def _ordered_findings(db: Session, scan: Scan) -> list[Finding]:
    findings = list(db.scalars(select(Finding).where(Finding.scan_id == scan.id)))
    findings.sort(key=lambda f: (-SEVERITY_RANK.get(f.severity, 0), f.tool, f.title))
    return findings


def build_report_data(db: Session, scan: Scan) -> dict:
    counts = scan.severity_counts or {sev: 0 for sev in SEVERITIES}
    return {
        "project": scan.project,
        "scan": scan,
        "counts": counts,
        "max_count": max([*counts.values(), 1]),
        "severities": SEVERITIES,
        "total": scan.total_findings,
        "findings": _ordered_findings(db, scan),
        "generated_at": datetime.now(timezone.utc),
    }


def report_json(db: Session, scan: Scan) -> dict:
    return {
        "generator": "TrioSec",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "project": {"id": scan.project.id, "name": scan.project.name},
        "scan": ScanOut.model_validate(scan).model_dump(mode="json"),
        "findings": [
            FindingOut.model_validate(f).model_dump(mode="json") for f in _ordered_findings(db, scan)
        ],
    }


def render_html(db: Session, scan: Scan) -> str:
    return _env.get_template("report.html").render(**build_report_data(db, scan))


def render_pdf(db: Session, scan: Scan) -> bytes:
    # Lazy import: WeasyPrint needs system libraries only present in the API image.
    from weasyprint import HTML

    return HTML(string=render_html(db, scan)).write_pdf()
