from functools import lru_cache
import os
from pathlib import Path
from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent

UNSAFE_ADMIN_PASSWORDS = {
    "ChangeMe123!",
    "replace-with-secure-admin-password",
}

UNSAFE_JWT_SECRET_KEYS = {
    "replace-with-a-long-random-secret",
}


def is_safe_admin_password(password: str) -> bool:
    return password not in UNSAFE_ADMIN_PASSWORDS and len(password) >= 10


class Settings(BaseSettings):
    project_name: str = "Sri Sri Wellbeing Chennai API"
    database_url: str = "mysql+pymysql://root:password@localhost:3306/srisriwellbeing"
    jwt_secret_key: str = "replace-with-a-long-random-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    password_reset_expire_minutes: int = 30
    admin_email: str = "admin@srisriwellbeingchennai.com"
    admin_password: str = "ChangeMe123!"
    seed_default_content: bool = False
    frontend_origin: str = "http://localhost:3000"
    frontend_origin_regex: str = (
        r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https://.*\.vercel\.app$"
    )
    mail_enabled: bool = False
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_timeout_seconds: int = 20
    smtp_local_hostname: str | None = None
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_from_email: str | None = None
    smtp_from_name: str = "Sri Sri Wellbeing Chennai"
    smtp_reply_to_email: str | None = None
    admin_reset_password_url: str | None = None
    admin_login_url: str | None = None

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def model_post_init(self, __context) -> None:
        render_enabled = os.getenv("RENDER", "").lower() == "true"
        production_enabled = render_enabled or os.getenv("ENVIRONMENT", "").lower() in {
            "prod",
            "production",
        }
        parsed = urlparse(self.database_url)
        host = (parsed.hostname or "").lower()

        # Support legacy env naming used in some deployments.
        if not self.smtp_username:
            legacy_username = os.getenv("SMTP_USER")
            if legacy_username:
                self.smtp_username = legacy_username
        if not self.smtp_password:
            legacy_password = os.getenv("SMTP_PASS") or os.getenv("SMTP_SECRET")
            if legacy_password:
                self.smtp_password = legacy_password

        # Port 465 usually expects implicit SSL instead of STARTTLS.
        if self.smtp_port == 465 and not self.smtp_use_ssl:
            self.smtp_use_ssl = True
            self.smtp_use_tls = False

        if render_enabled and host in {"localhost", "127.0.0.1"}:
            raise ValueError(
                "Invalid DATABASE_URL for Render: localhost points to the web service itself. "
                "Set DATABASE_URL to your MySQL service host, for example "
                "'mysql+pymysql://USER:PASSWORD@mysql:3306/DBNAME' or your external MySQL host."
            )

        if production_enabled:
            if self.jwt_secret_key in UNSAFE_JWT_SECRET_KEYS or len(self.jwt_secret_key) < 32:
                raise ValueError(
                    "Unsafe JWT_SECRET_KEY for production. Set JWT_SECRET_KEY to a unique secret "
                    "with at least 32 characters."
                )

    @property
    def is_production(self) -> bool:
        return os.getenv("RENDER", "").lower() == "true" or os.getenv("ENVIRONMENT", "").lower() in {
            "prod",
            "production",
        }

    @property
    def frontend_origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.frontend_origin.split(",") if origin.strip()]

    @property
    def password_reset_url(self) -> str:
        if self.admin_reset_password_url:
            return self.admin_reset_password_url.rstrip("/")
        origins = self.frontend_origins
        base_origin = origins[0] if origins else "http://localhost:3000"
        return f"{base_origin}/admin/reset-password"

    @property
    def login_url(self) -> str:
        if self.admin_login_url:
            return self.admin_login_url.rstrip("/")
        origins = self.frontend_origins
        base_origin = origins[0] if origins else "http://localhost:3000"
        return f"{base_origin}/admin/login"


@lru_cache
def get_settings() -> Settings:
    return Settings()
