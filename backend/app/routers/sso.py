"""Microsoft Entra ID single sign-on (OIDC authorization-code flow).

The backend drives the whole redirect dance and finishes by issuing the same
app JWT as password login, so every protected endpoint is untouched. Enabled
only when the four ENTRA_*/SSO_* settings are configured (see .env.example).
"""

from urllib.parse import quote

from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import settings
from app.deps import get_db
from app.models.user import User
from app.security import create_access_token
from app.services import audit_service
from app.services.audit_service import client_ip

router = APIRouter(prefix="/auth/sso", tags=["auth"])

# Entra app role (App registrations -> App roles) that maps to is_admin.
# Tokens without a roles claim leave locally-managed roles untouched.
ADMIN_ROLE = "TrioSec.Admin"

oauth = OAuth()
if settings.sso_enabled:
    oauth.register(
        name="entra",
        server_metadata_url=(
            f"https://login.microsoftonline.com/{settings.entra_tenant_id}"
            "/v2.0/.well-known/openid-configuration"
        ),
        client_id=settings.entra_client_id,
        client_secret=settings.entra_client_secret,
        client_kwargs={"scope": "openid profile email"},
    )


def _require_sso() -> None:
    if not settings.sso_enabled:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "SSO is not configured")


def _error_redirect(message: str) -> RedirectResponse:
    # The fragment never reaches server logs; the frontend callback page shows it.
    return RedirectResponse(f"/auth/callback#error={quote(message)}")


@router.get("/status")
def sso_status():
    return {"enabled": settings.sso_enabled}


@router.get("/login")
async def sso_login(request: Request):
    _require_sso()
    return await oauth.entra.authorize_redirect(request, settings.sso_redirect_uri)


@router.get("/callback")
async def sso_callback(request: Request, db: Session = Depends(get_db)):
    _require_sso()
    ip = client_ip(request)
    try:
        token = await oauth.entra.authorize_access_token(request)
    except OAuthError as exc:
        audit_service.record("login.failure", ip=ip, detail={"method": "sso", "reason": exc.error})
        return _error_redirect("Microsoft sign-in failed. Please try again.")

    claims = token.get("userinfo") or {}
    email = (claims.get("email") or claims.get("preferred_username") or "").strip().lower()
    if "@" not in email:
        audit_service.record("login.failure", ip=ip, detail={"method": "sso", "reason": "no_email_claim"})
        return _error_redirect("Your Microsoft account did not provide an email address.")

    roles = claims.get("roles")
    user = db.scalar(select(User).where(User.email == email))
    if user is None:
        user = User(
            email=email,
            hashed_password=None,
            is_admin=bool(roles and ADMIN_ROLE in roles),
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        audit_service.record(
            "user.create", actor=user, ip=ip, target=email,
            detail={"method": "sso", "is_admin": user.is_admin},
        )
    elif roles is not None and user.is_admin != (ADMIN_ROLE in roles):
        entra_admin = ADMIN_ROLE in roles
        other_admins = db.scalar(
            select(func.count()).select_from(User).where(
                User.is_admin.is_(True), User.is_active.is_(True), User.id != user.id
            )
        ) or 0
        # Entra app roles win when present, but never demote the last active admin.
        if entra_admin or other_admins > 0:
            user.is_admin = entra_admin
            db.commit()
            audit_service.record(
                "user.update", actor=user, ip=ip, target=email,
                detail={"method": "sso_role_sync", "is_admin": entra_admin},
            )

    if not user.is_active:
        audit_service.record(
            "login.failure", actor=user, ip=ip, target=email,
            detail={"method": "sso", "reason": "deactivated"},
        )
        return _error_redirect("This account has been deactivated.")

    audit_service.record("login.success", actor=user, ip=ip, detail={"method": "sso"})
    return RedirectResponse(f"/auth/callback#token={create_access_token(user.id)}")
