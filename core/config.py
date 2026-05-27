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
    cors_origin_regex: str = (
        r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|"
        r"(www\.)?kurrentschrift\.ink|api\.kurrentschrift\.ink)(:\d+)?$"
    )

    # ------------------------------------------------------------------ Admin auth
    # Cloudflare Access (Zero Trust) verifies a Google identity at the edge and
    # forwards Cf-Access-Jwt-Assertion to Cloud Run; api/auth.py verifies the
    # JWT against the team's JWKS endpoint. Leave unset for local dev — the
    # X-Admin-Token fallback handles CI / break-glass access.
    cf_access_team_domain: str | None = None
    cf_access_aud: str | None = None
    admin_token: str | None = None
    # Comma-separated env value parsed into a tuple. Browser users with a valid
    # JWT but an email not in this list receive 403 — required for the JWT path
    # to authorize anyone.
    admin_allowed_emails_raw: str = ""

    @property
    def is_production(self) -> bool:
        return self.environment.lower() == "production"

    @property
    def is_development(self) -> bool:
        return self.environment.lower() == "development"

    @property
    def is_database_configured(self) -> bool:
        return bool(self.database_url or self.instance_connection_name)

    @property
    def admin_allowed_emails(self) -> tuple[str, ...]:
        return tuple(e.strip().lower() for e in self.admin_allowed_emails_raw.split(",") if e.strip())


settings = Settings()
