"""Settings — paths into the existing /mvp/canonical/ data tree.

The API is a thin web layer on top of the existing CLI pipeline; it reads
and writes the same JSON files that mvp.tools.trace_skeleton has been
producing, so they stay one source of truth.
"""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Runtime settings. Defaults work for local dev; override via env for Cloud Run."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    repo_root: Path = REPO_ROOT
    chart_path: Path = REPO_ROOT / "data" / "sources" / "loth-1866" / "chart.jpg"
    bboxes_json: Path = REPO_ROOT / "mvp" / "canonical" / "loth_bboxes.json"
    canonical_dir: Path = REPO_ROOT / "mvp" / "canonical"
    cors_origin_regex: str = r"http://(localhost|127\.0\.0\.1|192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+):\d+"


settings = Settings()
