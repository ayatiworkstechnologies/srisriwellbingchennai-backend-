from functools import lru_cache
import os
from pathlib import Path
from urllib.parse import urlparse

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    project_name: str = "Sri Sri Wellbeing Chennai API"
    database_url: str = "mysql+pymysql://root:password@localhost:3306/srisriwellbeing"
    jwt_secret_key: str = "change-this-secret-key"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    admin_email: str = "admin@srisriwellbeingchennai.com"
    admin_password: str = "ChangeMe123!"
    frontend_origin: str = "http://localhost:3000"
    frontend_origin_regex: str = (
        r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$|^https://.*\.vercel\.app$"
    )
    mail_enabled: bool = False
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    smtp_use_ssl: bool = False
    smtp_from_email: str | None = None
    smtp_from_name: str = "Sri Sri Wellbeing Chennai"

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def model_post_init(self, __context) -> None:
        render_enabled = os.getenv("RENDER", "").lower() == "true"
        parsed = urlparse(self.database_url)
        host = (parsed.hostname or "").lower()

        # Support legacy env naming used in some deployments.
        if not self.smtp_username:
            legacy_username = os.getenv("SMTP_USER")
            if legacy_username:
                self.smtp_username = legacy_username

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

    @property
    def frontend_origins(self) -> list[str]:
        return [origin.strip().rstrip("/") for origin in self.frontend_origin.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
