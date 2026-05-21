"""Centralised configuration via pydantic-settings.

Loaded once at process start from `.env` + environment variables. Import the
singleton: `from core.config import settings`.
"""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore")

    # ------------------------------------------------------------------ Database
    database_url: str | None = None
    instance_connection_name: str | None = None
    db_user: str = "postgres"
    db_pass: str = ""
    db_name: str = "kurrentschrift"

    # ------------------------------------------------------------------ App
    environment: str = "development"
    port: int = 8000

    # ------------------------------------------------------------------ Paths
    repo_root: Path = REPO_ROOT

    # ------------------------------------------------------------------ CORS
    cors_origin_regex: str = r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+)(:\d+)?$"

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    @property
    def is_database_configured(self) -> bool:
        return bool(self.database_url or self.instance_connection_name)


settings = Settings()
