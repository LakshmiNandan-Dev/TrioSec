from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.deps import get_current_admin, get_db
from app.models.user import User
from app.schemas.auth import UserOut
from app.schemas.user import UserCreate, UserUpdate
from app.security import hash_password
from app.services import audit_service
from app.services.audit_service import client_ip

router = APIRouter(prefix="/users", tags=["users"], dependencies=[Depends(get_current_admin)])


def _active_admin_count(db: Session) -> int:
    return db.scalar(
        select(func.count()).select_from(User).where(User.is_admin.is_(True), User.is_active.is_(True))
    ) or 0


def _get_user(db: Session, user_id: int) -> User:
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "User not found")
    return user


@router.get("", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.scalars(select(User).order_by(User.created_at)).all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    request: Request,
    current: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    email = payload.email.strip().lower()
    if db.scalar(select(User).where(User.email == email)) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "A user with this email already exists")
    user = User(
        email=email,
        hashed_password=hash_password(payload.password),
        is_admin=payload.is_admin,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    audit_service.record(
        "user.create", actor=current, ip=client_ip(request), target=email,
        detail={"is_admin": user.is_admin},
    )
    return user


@router.patch("/{user_id}", response_model=UserOut)
def update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    current: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = _get_user(db, user_id)

    # Guard against locking everyone out or yourself.
    demoting = (payload.is_admin is False) or (payload.is_active is False)
    if user.id == current.id and demoting:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, "You cannot remove your own admin role or deactivate yourself"
        )
    if user.is_admin and user.is_active and demoting and _active_admin_count(db) <= 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "At least one active admin must remain")

    if payload.is_admin is not None:
        user.is_admin = payload.is_admin
    if payload.is_active is not None:
        user.is_active = payload.is_active
    if payload.password:
        user.hashed_password = hash_password(payload.password)
    db.commit()
    db.refresh(user)
    audit_service.record(
        "user.update", actor=current, ip=client_ip(request), target=user.email,
        detail={
            "is_admin": payload.is_admin,
            "is_active": payload.is_active,
            "password_reset": bool(payload.password),
        },
    )
    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    request: Request,
    current: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    user = _get_user(db, user_id)
    if user.id == current.id:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "You cannot delete your own account")
    if user.is_admin and user.is_active and _active_admin_count(db) <= 1:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "At least one active admin must remain")
    email = user.email
    db.delete(user)
    db.commit()
    audit_service.record("user.delete", actor=current, ip=client_ip(request), target=email)
