from functools import lru_cache
from pathlib import Path

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

    model_config = SettingsConfigDict(
        env_file=BASE_DIR / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
