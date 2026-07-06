from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.project import Project
from app.models.scan import Scan
from app.models.user import User
from app.schemas.scan import ScanCreate, ScanOut
from app.services import audit_service, scan_service
from app.services.audit_service import client_ip
from app.services.path_service import TargetValidationError

router = APIRouter(prefix="/scans", tags=["scans"], dependencies=[Depends(get_current_user)])


def _get_scan(db: Session, scan_id: int) -> Scan:
    scan = db.get(Scan, scan_id)
    if scan is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Scan not found")
    return scan


@router.post("", response_model=ScanOut, status_code=status.HTTP_201_CREATED)
def create_scan(
    payload: ScanCreate,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if db.get(Project, payload.project_id) is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    try:
        scan = scan_service.create_scan(db, payload, authorized_by=user.email)
    except TargetValidationError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc)) from exc
    audit_service.record(
        "scan.create",
        actor=user,
        ip=client_ip(request),
        target=scan.dast_url or scan.target_value,
        detail={"scan_id": scan.id, "scan_types": scan.scan_types, "project_id": scan.project_id},
    )
    return scan


@router.get("", response_model=list[ScanOut])
def list_scans(project_id: int | None = None, limit: int = 50, db: Session = Depends(get_db)):
    query = select(Scan).order_by(Scan.created_at.desc()).limit(min(limit, 200))
    if project_id is not None:
        query = query.where(Scan.project_id == project_id)
    return db.scalars(query).all()


@router.get("/{scan_id}", response_model=ScanOut)
def get_scan(scan_id: int, db: Session = Depends(get_db)):
    return _get_scan(db, scan_id)


@router.get("/{scan_id}/logs")
def get_scan_logs(scan_id: int, db: Session = Depends(get_db)):
    return {"logs": _get_scan(db, scan_id).logs or ""}


@router.post("/{scan_id}/cancel", response_model=ScanOut)
def cancel_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = _get_scan(db, scan_id)
    try:
        return scan_service.cancel_scan(db, scan)
    except ValueError as exc:
        raise HTTPException(status.HTTP_409_CONFLICT, str(exc)) from exc
