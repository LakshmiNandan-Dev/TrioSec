from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.project import Project
from app.models.scan import Scan
from app.schemas.finding import FindingBrief
from app.schemas.project import ProjectCreate, ProjectOut, ProjectUpdate
from app.schemas.scan import CompareResult, TrendPoint
from app.services import scan_service
from app.services.crypto import encrypt_str

router = APIRouter(prefix="/projects", tags=["projects"], dependencies=[Depends(get_current_user)])


def _get_project(db: Session, project_id: int) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Project not found")
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db)):
    return db.scalars(select(Project).order_by(Project.created_at.desc())).all()


@router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Project).where(Project.name == payload.name)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "A project with this name already exists")
    data = payload.model_dump()
    token = data.pop("git_token", None)
    project = Project(**data)
    if token:
        project.git_token_encrypted = encrypt_str(token)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectOut)
def get_project(project_id: int, db: Session = Depends(get_db)):
    return _get_project(db, project_id)


@router.put("/{project_id}", response_model=ProjectOut)
def update_project(project_id: int, payload: ProjectUpdate, db: Session = Depends(get_db)):
    project = _get_project(db, project_id)
    data = payload.model_dump(exclude_unset=True)
    token = data.pop("git_token", None)
    clear_token = data.pop("clear_git_token", False)
    for key, value in data.items():
        setattr(project, key, value)
    if clear_token:
        project.git_token_encrypted = None
    elif token:
        project.git_token_encrypted = encrypt_str(token)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)):
    db.delete(_get_project(db, project_id))
    db.commit()


@router.get("/{project_id}/trends", response_model=list[TrendPoint])
def project_trends(project_id: int, db: Session = Depends(get_db)):
    _get_project(db, project_id)
    return scan_service.project_trends(db, project_id)


@router.get("/{project_id}/compare", response_model=CompareResult)
def compare_scans(project_id: int, base: int, head: int, db: Session = Depends(get_db)):
    _get_project(db, project_id)
    for scan_id in (base, head):
        scan = db.get(Scan, scan_id)
        if scan is None or scan.project_id != project_id:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"Scan {scan_id} not found in this project")
    added, fixed, unchanged = scan_service.compare_scans(db, base, head)
    return CompareResult(
        base_scan_id=base,
        head_scan_id=head,
        added=[FindingBrief.model_validate(f) for f in added],
        fixed=[FindingBrief.model_validate(f) for f in fixed],
        unchanged_count=unchanged,
    )
