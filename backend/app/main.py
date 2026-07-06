from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select

from app.config import settings
from app.db import SessionLocal
from app.models import AppSetting, User
from app.routers import audit, auth, findings, health, projects, reports, scans, users
from app.routers import settings as settings_router
from app.security import hash_password


def seed_initial_data() -> None:
    with SessionLocal() as db:
        if db.scalar(select(User).limit(1)) is None:
            db.add(
                User(
                    email=settings.admin_email.strip().lower(),
                    hashed_password=hash_password(settings.admin_password),
                )
            )
        if db.get(AppSetting, 1) is None:
            db.add(AppSetting(id=1, smtp_from_address=settings.admin_email))
        db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings.validate_secrets()
    seed_initial_data()
    yield


app = FastAPI(title="TrioSec API", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for router in (
    health.router,
    auth.router,
    projects.router,
    scans.router,
    findings.router,
    reports.router,
    settings_router.router,
    users.router,
    audit.router,
):
    app.include_router(router, prefix="/api")
