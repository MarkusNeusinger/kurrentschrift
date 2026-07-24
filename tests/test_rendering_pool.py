"""Unit tests for the pooled nib/pen memoisation in `api.rendering`.

The TTL cache is the mechanism that keeps admin trace → public render
coherent (a stale entry would silently ship the wrong pen for up to 10
minutes) — test it with a fake repository and a frozen `time.monotonic`, no
DB. The caches are module-level; a fixture snapshots and restores them so no
state leaks into the HTTP suites.
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from fastapi import HTTPException

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
    payload_snapshot = dict(rendering._payload_cache)
    rendering._nib_cache.clear()
    rendering._pen_cache.clear()
    rendering._payload_cache.clear()
    _FakeRepo.calls = 0
    monkeypatch.setattr(rendering, "TemplateRepository", _FakeRepo)
    clock = {"now": 1000.0}
    monkeypatch.setattr(rendering.time, "monotonic", lambda: clock["now"])
    yield clock
    rendering._nib_cache.clear()
    rendering._nib_cache.update(nib_snapshot)
    rendering._pen_cache.clear()
    rendering._pen_cache.update(pen_snapshot)
    rendering._payload_cache.clear()
    rendering._payload_cache.update(payload_snapshot)


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


# ------------------------------------------------------- render-payload memo


def _render_ctx(width_resolver: str = "pressure") -> rendering.RenderContext:
    pen = rendering.PenStyle(kind="pressure", hairline_half=0.04)
    return rendering.RenderContext("kurrent", [2.0, 1.0, 2.0], 50.0, width_resolver, None, pen)


@pytest.fixture
def _counted_render(monkeypatch):
    """Replace the real payload computation with a counting stub that returns
    a fresh (mutable) dict per call — so cache hits are provable by identity
    and call count, without dragging real template geometry into the test."""
    calls = {"n": 0}

    def fake_render(glyph_row, style_ratio, width_resolver, constant_nib_units, pen=None):
        calls["n"] += 1
        return {"outline_paths": [[[[0.0, 0.0], [1.0, 0.0]]]], "advance": glyph_row["advance"], "seq": calls["n"]}

    monkeypatch.setattr(rendering, "render_payload_for_template", fake_render)
    return calls


def test_render_payload_cached_serves_memo_and_misses_on_updated_at(_isolated_pool, _counted_render):
    ctx = _render_ctx()
    row = {"advance": 0.5}
    first = rendering.render_payload_cached(row, "n", 7, "2026-07-24T10:00:00", ctx)
    again = rendering.render_payload_cached(row, "n", 7, "2026-07-24T10:00:00", ctx)
    assert again is first  # identical request → the memoised payload, not a recompute
    assert _counted_render["n"] == 1

    # An admin write bumps updated_at → new key → fresh payload.
    fresh = rendering.render_payload_cached(row, "n", 7, "2026-07-24T11:00:00", ctx)
    assert fresh is not first
    assert _counted_render["n"] == 2


def test_render_payload_cached_repeat_equals_first_after_copy_annotate(_isolated_pool, _counted_render):
    """The router pattern `{**payload, "glyph_key": k}` must leave the shared
    memo entry untouched — a repeated request serves an equal payload."""
    ctx = _render_ctx()
    first = rendering.render_payload_cached({"advance": 0.5}, "n", 7, "t1", ctx)
    snapshot = dict(first)
    annotated = {**first, "glyph_key": "n"}
    assert "glyph_key" in annotated and "glyph_key" not in first
    again = rendering.render_payload_cached({"advance": 0.5}, "n", 7, "t1", ctx)
    assert again == snapshot
    assert _counted_render["n"] == 1


def test_render_payload_cache_invalidation_and_ttl(_isolated_pool, _counted_render):
    clock = _isolated_pool
    ctx = _render_ctx()
    rendering.render_payload_cached({"advance": 0.5}, "n", 7, "t1", ctx)
    rendering.invalidate_pooled_style("kurrent")
    rendering.render_payload_cached({"advance": 0.5}, "n", 7, "t1", ctx)
    assert _counted_render["n"] == 2  # style invalidation dropped the entry

    rendering.invalidate_pooled_nib("kurrent", "loth-1866")
    rendering.render_payload_cached({"advance": 0.5}, "n", 7, "t1", ctx)
    assert _counted_render["n"] == 3  # per-source invalidation clears the style's payloads too

    clock["now"] += rendering._NIB_TTL_S + 1
    rendering.render_payload_cached({"advance": 0.5}, "n", 7, "t1", ctx)
    assert _counted_render["n"] == 4  # TTL elapsed → recompute (out-of-band-write safety net)


def test_render_payload_cache_bounded_eviction(_isolated_pool, _counted_render):
    ctx = _render_ctx()
    for i in range(rendering._PAYLOAD_CACHE_MAX + 5):
        rendering.render_payload_cached({"advance": 0.5}, f"g{i}", i, "t1", ctx)
    assert len(rendering._payload_cache) == rendering._PAYLOAD_CACHE_MAX


async def test_resolve_style_unknown_style_500_without_internal_detail(monkeypatch):
    """A source referencing a missing style is a server-side integrity error:
    the 500 body must stay generic — the ids belong in the log, not the wire."""

    class _NoStyleRepo:
        def __init__(self, _db):
            pass

        async def get(self, _style_id):
            return None

    monkeypatch.setattr(rendering, "StyleRepository", _NoStyleRepo)
    source = SimpleNamespace(id="loth-1866", style_id="gone")
    with pytest.raises(HTTPException) as exc:
        await rendering.resolve_style(source, None)
    assert exc.value.status_code == 500
    assert "gone" not in exc.value.detail and "loth-1866" not in exc.value.detail
