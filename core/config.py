"""Centralised configuration via pydantic-settings.

Loaded once at process start from `.env` + environment variables. Import the
singleton: `from core.config import settings`.
"""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parent.parent

# Production allows exactly the public site origin; development additionally
# accepts localhost/LAN origins (any port) for the Vite dev server and
# stylus-on-tablet testing against a dev machine's LAN IP.
_CORS_PRODUCTION_REGEX = r"^https://(www\.)?kurrentschrift\.ink$"
_CORS_DEVELOPMENT_REGEX = (
    r"^https?://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|"
    r"(www\.)?kurrentschrift\.ink)(:\d+)?$"
)


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
    # The crawler pages the app build renders (app/src/lib/seo/prerender.ts →
    # app/prerender/, committed). api/Dockerfile copies the directory under the
    # same relative path, so the default holds in the image and in a checkout;
    # `PRERENDER_DIR` overrides it (tests point it at a temp dir).
    prerender_dir: Path = REPO_ROOT / "app" / "prerender"

    # ------------------------------------------------------------------ Bot analytics
    # Crawler page reads (the /seo-proxy path) are reported server-side to a
    # SECOND Plausible site, never the human one (api/analytics.py). On by
    # default only in production — a dev run must not write to the live bot
    # site; `BOT_ANALYTICS=true|false` overrides either way.
    plausible_bots_domain: str = "bots.kurrentschrift.ink"
    bot_analytics: bool | None = None

    @property
    def bot_analytics_enabled(self) -> bool:
        if self.bot_analytics is not None:
            return self.bot_analytics
        return self.environment == "production"

    # ------------------------------------------------------------------ Rate limit
    # Two token buckets per client, both in `api/rate_limit.py`, narrow first.
    #
    # NARROW — the compose path `/write/word*`, the one public read whose cost
    # is set by the CALLER's input: a unique text misses every cache and, at the
    # 160-character maximum, costs ~0.8 s of CPU and ~1.6 MB of egress. 60/min
    # sustained with a burst of 20 sits far above any human page (the
    # Schreibtafel composes one word per interaction) and far below a scripted
    # harvest.
    write_rate_limit_per_min: int = 60
    write_rate_limit_burst: int = 20

    # WIDE — every other route, GET and HEAD included (owner decision
    # 2026-09-02: block extreme use so no one can run up the bill or take the
    # service down with sheer request volume). A PROPOSAL, not a measurement:
    # 600/min with a burst of 120 is an order of magnitude above what browsing
    # the site produces — a Tafel page load is a handful of batched requests, a
    # quiz round one — and well under what walking the API in a loop needs.
    # It counts at the ORIGIN, so edge-cached reads never reach it and only
    # cache misses spend a token; `/health` and the prerendered `/seo-proxy`
    # pages are exempt (rate_limit.py says why). Either
    # `*_RATE_LIMIT_PER_MIN=0` disables that bucket.
    public_rate_limit_per_min: int = 600
    public_rate_limit_burst: int = 120

    # ------------------------------------------------------------------ CORS
    # Explicit env override wins; otherwise the effective regex is picked per
    # environment (see `cors_allow_origin_regex`) so the localhost/LAN dev
    # conveniences never widen the production allow-list.
    cors_origin_regex: str | None = None

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

    # ------------------------------------------------------------------ Origin gate
    # Shared secret between the Cloudflare edge and this service: a Transform
    # Rule stamps `X-Origin-Secret` onto every request it proxies for
    # api.kurrentschrift.ink, and `api/origin_gate.py` refuses anything else
    # with 403. That closes the direct `*.run.app` door, which otherwise
    # bypasses the Cloudflare rate-limiting rule, the WAF and the cache —
    # `ingress=all` on both services, no load balancer (it would cost more per
    # month than the project).
    #
    # UNSET MEANS OFF, and that is the rollback: remove the variable from the
    # Cloud Run service and the gate is gone without a deploy. Local dev and
    # the test suite never set it. `/health` and `/seo-proxy/…` are exempt even
    # when it is set — see origin_gate.py for why each one has to be.
    origin_secret: str | None = None

    # Secret Manager stores whatever bytes the version was created with, and a
    # value piped in via `echo` carries a trailing newline. Cloud Run injects
    # those bytes verbatim (`--set-secrets`), so the setting would keep the
    # newline while an HTTP header physically cannot transport one — the
    # X-Admin-Token break-glass path then rejects every request with 401 and no
    # token value can ever fix it. Strip at the source rather than at each use
    # site; whitespace is meaningless in all five Secret-Manager-backed values,
    # and `origin_secret` is compared against a header for exactly the same
    # reason the ADMIN_TOKEN incident of 2026-08 happened.
    @field_validator(
        "database_url", "cf_access_team_domain", "cf_access_aud", "admin_token", "origin_secret", mode="after"
    )
    @classmethod
    def _strip_secret(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @property
    def cors_allow_origin_regex(self) -> str:
        """The CORS origin regex the app should serve with (env override wins)."""
        if self.cors_origin_regex:
            return self.cors_origin_regex
        return _CORS_PRODUCTION_REGEX if self.is_production else _CORS_DEVELOPMENT_REGEX

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
