from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.finding import Finding
from app.schemas.finding import FindingOut, FindingPage

router = APIRouter(prefix="/findings", tags=["findings"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=FindingPage)
def list_findings(
    scan_id: int,
    severity: str | None = None,
    tool: str | None = None,
    category: str | None = None,
    is_new: bool | None = None,
    q: str | None = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    filters = [Finding.scan_id == scan_id]
    if severity:
        filters.append(Finding.severity == severity)
    if tool:
        filters.append(Finding.tool == tool)
    if category:
        filters.append(Finding.category == category)
    if is_new is not None:
        filters.append(Finding.is_new == is_new)
    if q:
        like = f"%{q}%"
        filters.append(
            or_(
                Finding.title.ilike(like),
                Finding.file_path.ilike(like),
                Finding.package_name.ilike(like),
                Finding.cve.ilike(like),
                Finding.rule_id.ilike(like),
            )
        )

    total = db.scalar(select(func.count()).select_from(Finding).where(*filters)) or 0
    severity_order = func.array_position(
        func.string_to_array("critical,high,medium,low,info", ","), Finding.severity
    )
    items = db.scalars(
        select(Finding)
        .where(*filters)
        .order_by(severity_order, Finding.tool, Finding.id)
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()
    return FindingPage(
        items=[FindingOut.model_validate(f) for f in items],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/{finding_id}", response_model=FindingOut)
def get_finding(finding_id: int, db: Session = Depends(get_db)):
    finding = db.get(Finding, finding_id)
    if finding is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Finding not found")
    return finding
