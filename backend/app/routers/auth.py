from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.auth import ChangePasswordRequest, LoginRequest, TokenResponse, UserOut
from app.security import create_access_token, hash_password, verify_password
from app.services import audit_service
from app.services.audit_service import client_ip

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, request: Request, db: Session = Depends(get_db)):
    ip = client_ip(request)
    email = payload.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(payload.password, user.hashed_password):
        audit_service.record("login.failure", ip=ip, target=email, detail={"reason": "bad_credentials"})
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid email or password")
    if not user.is_active:
        audit_service.record("login.failure", actor=user, ip=ip, target=email, detail={"reason": "deactivated"})
        raise HTTPException(status.HTTP_403_FORBIDDEN, "This account has been deactivated")
    audit_service.record("login.success", actor=user, ip=ip)
    return TokenResponse(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.post("/change-password")
def change_password(
    payload: ChangePasswordRequest,
    request: Request,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if user.hashed_password is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "This account signs in with Microsoft SSO and has no local password",
        )
    if not verify_password(payload.current_password, user.hashed_password):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Current password is incorrect")
    user.hashed_password = hash_password(payload.new_password)
    db.commit()
    audit_service.record("password.change", actor=user, ip=client_ip(request))
    return {"changed": True}
