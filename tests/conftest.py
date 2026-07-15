"""Pytest fixtures: a synthetic chart + bbox so pipeline tests don't depend on
real data, plus the in-memory HTTP `api` harness shared by the API suites."""

from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture
def synthetic_chart() -> np.ndarray:
    """800x800 white grayscale ([0,1] float) with a thick black '|' downstroke
    from (400, 200) to (400, 600). Useful as a stand-in for a Loth-style glyph.
    """
    img = np.ones((800, 800), dtype=np.float32)
    img[200:600, 392:408] = 0.05  # 16px wide vertical bar
    return img


@pytest.fixture
def synthetic_bbox() -> dict:
    """Bbox that fully contains the synthetic glyph and sets baseline/midband
    so the x-height pixel unit is 100 (== a 1.0 unit in template coords).
    """
    return {
        "y0": 100,
        "y1": 700,
        "x0": 300,
        "x1": 500,
        "mask_strokes": [],
        "baseline_y": 600,
        "midband_y": 500,
        "n_anchors": 30,
    }


@pytest.fixture
def synthetic_chart_path(tmp_path, synthetic_chart) -> str:
    """Persist the synthetic chart to disk and return its absolute path."""
    from PIL import Image

    out = tmp_path / "chart.png"
    Image.fromarray((synthetic_chart * 255).astype(np.uint8), mode="L").save(out)
    return str(out)


@pytest.fixture
async def api(monkeypatch):
    """The FastAPI app wired to a fresh in-memory aiosqlite DB.

    - `get_db` is dependency-overridden with sessions off a StaticPool engine
      (one shared connection, so seeded rows are visible to request sessions);
    - `api.dependencies.is_db_configured` is forced True so `require_db` passes
      regardless of the host's real DATABASE_URL / .env;
    - a known ADMIN_TOKEN is configured (individual tests may unset it).

    Harness/client classes live in `tests/api_harness.py`.
    """
    from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
    from sqlalchemy.pool import StaticPool

    import api.dependencies as api_dependencies
    from api.main import app
    from core.config import settings
    from core.database import Base, get_db
    from tests.api_harness import ADMIN_TOKEN, AsgiClient, Harness

    engine = create_async_engine("sqlite+aiosqlite://", poolclass=StaticPool)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_get_db():
        async with session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _override_get_db
    monkeypatch.setattr(api_dependencies, "is_db_configured", lambda: True)
    monkeypatch.setattr(settings, "admin_token", ADMIN_TOKEN)

    try:
        yield Harness(AsgiClient(app), session_maker)
    finally:
        app.dependency_overrides.pop(get_db, None)
        await engine.dispose()
