from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

PLACEHOLDER_SECRETS = {"", "changeme", "change-me", "secret"}


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str = "redis://redis:6379/0"

    jwt_secret: str
    jwt_expires_minutes: int = 720
    admin_email: str = "admin@triosec.local"
    admin_password: str = "change-me-admin-password"

    # Key material for encrypting the SMTP password at rest (hashed into a Fernet key).
    secret_encryption_key: str

    # Container-side mount of the user's code workspace.
    workspace_container_root: str = "/workspace"
    # Host-side path of the same directory, so users may paste absolute host paths.
    workspace_root: str = ""

    zap_base_url: str = "http://zap:8090"
    zap_api_key: str = ""
    # DAST spider bounds — a large or JS-heavy site can crawl for a very long time,
    # so cap it. ZAP stops the spider itself after this many minutes; the scan then
    # proceeds with whatever was crawled instead of failing.
    zap_spider_max_duration_min: int = 5
    zap_spider_max_depth: int = 5

    # Extra CORS origins for local frontend development (vite dev server).
    cors_origins: str = "http://localhost:5173"

    def validate_secrets(self) -> None:
        if self.jwt_secret.strip().lower() in PLACEHOLDER_SECRETS:
            raise RuntimeError("JWT_SECRET is unset or a placeholder; refusing to start.")
        if self.secret_encryption_key.strip().lower() in PLACEHOLDER_SECRETS:
            raise RuntimeError("SECRET_ENCRYPTION_KEY is unset or a placeholder; refusing to start.")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
