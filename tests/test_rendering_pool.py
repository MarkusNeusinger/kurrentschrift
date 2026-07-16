"""Unit tests for the pooled nib/pen memoisation in `api.rendering`.

The TTL cache is the mechanism that keeps admin trace → public render
coherent (a stale entry would silently ship the wrong pen for up to 10
minutes) — test it with a fake repository and a frozen `time.monotonic`, no
DB. The caches are module-level; a fixture snapshots and restores them so no
state leaks into the HTTP suites.
"""

from __future__ import annotations

import pytest

from api import rendering


class _FakeRepo:
    """Stands in for TemplateRepository: counts the O(all-templates) scans."""

    calls = 0
    profiles: list[list[float]] = [[0.04, 0.05, 0.06], [0.05, 0.05, 0.07]]

    def __init__(self, _db):
        pass

    async def half_widths_for_source(self, style_id: str, source_id: str) -> list[list[float]]:
        _FakeRepo.calls += 1
        return _FakeRepo.profiles


@pytest.fixture(autouse=True)
def _isolated_pool(monkeypatch):
    nib_snapshot = dict(rendering._nib_cache)
    pen_snapshot = dict(rendering._pen_cache)
    rendering._nib_cache.clear()
    rendering._pen_cache.clear()
    _FakeRepo.calls = 0
    monkeypatch.setattr(rendering, "TemplateRepository", _FakeRepo)
    clock = {"now": 1000.0}
    monkeypatch.setattr(rendering.time, "monotonic", lambda: clock["now"])
    yield clock
    rendering._nib_cache.clear()
    rendering._nib_cache.update(nib_snapshot)
    rendering._pen_cache.clear()
    rendering._pen_cache.update(pen_snapshot)


async def test_pooled_pen_caches_within_ttl_and_recomputes_after(_isolated_pool):
    clock = _isolated_pool
    pen = await rendering.pooled_pen(None, "kurrent", "loth", "pressure")
    assert pen is not None and pen.kind == "pressure"
    again = await rendering.pooled_pen(None, "kurrent", "loth", "pressure")
    assert again is pen
    assert _FakeRepo.calls == 1  # second call served from the cache

    clock["now"] += rendering._NIB_TTL_S + 1
    await rendering.pooled_pen(None, "kurrent", "loth", "pressure")
    assert _FakeRepo.calls == 2  # TTL elapsed → fresh scan


async def test_pooled_constant_nib_caches_and_invalidates(_isolated_pool):
    nib = await rendering.pooled_constant_nib(None, "suetterlin", "s1922")
    assert nib is not None and nib > 0
    await rendering.pooled_constant_nib(None, "suetterlin", "s1922")
    assert _FakeRepo.calls == 1

    rendering.invalidate_pooled_nib("suetterlin", "s1922")
    await rendering.pooled_constant_nib(None, "suetterlin", "s1922")
    assert _FakeRepo.calls == 2  # explicit invalidation → fresh scan


async def test_non_pooled_resolver_returns_none_without_scanning(_isolated_pool):
    assert await rendering.pooled_pen(None, "suetterlin", "s1922", "constant") is None
    assert _FakeRepo.calls == 0
