"""Style resolution + source-pooled nib, shared by the templates and write routers.

The pooled constant nib (architektur.md §5: one Gleichzug pen per source) is an
O(all-templates) JSONB scan whose result only changes when a template of the
source is written — memoise it per (style, source) with explicit invalidation
from the admin write endpoints. Single-process cache by design: the service
runs one instance (max-instances=1) and every template write flows through this
process; the TTL is the safety net for out-of-band writes (psql, migrations).
"""

import logging
import statistics
import time
from dataclasses import dataclass

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import Source, StyleRepository, TemplateRepository
from core.pipeline import render_payload_for_template
from core.widths import BroadNib, PenStyle


logger = logging.getLogger(__name__)

_NIB_TTL_S = 600.0
# (style_id, source_id) -> (pooled nib radius in x-height units or None, computed_at)
_nib_cache: dict[tuple[str, str], tuple[float | None, float]] = {}
# (style_id, source_id, width_resolver) -> (PenStyle or None, computed_at)
_pen_cache: dict[tuple[str, str, str], tuple[PenStyle | None, float]] = {}
# Memoised `render_payload_for_template` outputs: the silhouette/centerline
# sampling is a pure function of (template row content, resolved render
# context), yet dominates the public /write CPU because the same few dozen
# templates are re-sampled on every request. Keyed by the template's identity
# + `updated_at` stamp + every render input, so an admin write naturally
# misses; the explicit style invalidation below and the shared TTL are the
# same safety nets the nib/pen caches use.
# key (see `render_payload_cached`) -> (payload dict, computed_at)
_PAYLOAD_CACHE_MAX = 512  # ~30 glyphs/source at a handful of sources — 512 is generous
_payload_cache: dict[tuple, tuple[dict, float]] = {}


async def resolve_style(source: Source, db: AsyncSession) -> tuple[str, list[float], float, str]:
    """Return (style_id, resolved style_ratio, resolved slant_deg, width_resolver) for a source.

    A source may override ratio/slant per chart (null => use the style); the
    width resolver is a pure style property a source can never override
    (architektur.md §5).
    """
    style = await StyleRepository(db).get(source.style_id)
    if style is None:
        # Referential-integrity detail is server-internal — log it, keep the
        # response body generic.
        logger.error("source %r references unknown style %r", source.id, source.style_id)
        raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR, detail="internal style resolution error")
    style_ratio = list(source.style_ratio) if source.style_ratio is not None else list(style.default_style_ratio)
    slant_deg = float(source.slant_deg) if source.slant_deg is not None else float(style.default_slant_deg)
    return style.id, style_ratio, slant_deg, style.width_resolver


async def pooled_constant_nib(db: AsyncSession, style_id: str, source_id: str) -> float | None:
    """Source-wide mean nib radius (x-height units) for a constant-width style.

    architektur.md §5: a Gleichzug script is written with ONE constant nib, so the
    rendered thickness should be the source's mean — not each glyph's own measured
    constant (which varies with per-crop quantisation: 0.062–0.081 here). Pools the
    median half-width of every template traced from this chart source; the resolver
    override in the render/diagnostic payloads then draws all of them at this one
    value. Returns None when nothing is traced yet (caller falls back to per-glyph
    widths). Memoised — see module docstring.
    """
    key = (style_id, source_id)
    now = time.monotonic()
    hit = _nib_cache.get(key)
    if hit is not None and now - hit[1] < _NIB_TTL_S:
        return hit[0]
    profiles = await TemplateRepository(db).half_widths_for_source(style_id, source_id)
    nibs = [statistics.median(hw) for hw in profiles if hw]
    value = float(statistics.mean(nibs)) if nibs else None
    _nib_cache[key] = (value, now)
    return value


def _percentile(sorted_values: list[float], q: float) -> float:
    """Percentile by half-up-rounded index on an ascending list (q in [0, 1]):
    the element at ⌊q·(n−1) + 0.5⌋ — no interpolation, no banker's rounding."""
    idx = min(len(sorted_values) - 1, max(0, int(q * (len(sorted_values) - 1) + 0.5)))
    return sorted_values[idx]


def pen_from_profiles(width_resolver: str, profiles: list[list[float]]) -> PenStyle | None:
    """Pure calibration core of `pooled_pen` — see its docstring for the
    per-resolver rules. Split out so the maths is unit-testable without a DB."""
    if width_resolver not in ("pressure", "broad_nib"):
        return None
    flat = sorted(float(w) for hw in profiles for w in (hw or []))
    if width_resolver == "pressure":
        return PenStyle(kind="pressure", hairline_half=_percentile(flat, 0.10) if flat else None)
    if flat:
        width_units = max(2 * _percentile(flat, 0.95), 1e-3)
        edge_fraction = min(max((2 * _percentile(flat, 0.10)) / width_units, 0.05), 0.5)
        nib = BroadNib(width_units=width_units, edge_fraction=edge_fraction)
    else:
        nib = BroadNib()
    return PenStyle(kind="broad_nib", nib=nib)


async def pooled_pen(db: AsyncSession, style_id: str, source_id: str, width_resolver: str) -> PenStyle | None:
    """Render-time pen for a style, calibrated from the source's measurements.

    - ``pressure`` → the pooled Haarstrich half-width (P10 of all measured
      half-widths of the source): generated strokes (Übergänge, Endstrich)
      are hairlines by Spitzfeder physics, but the ink they are drawn at is
      this hand's own hairline, not a constant.
    - ``broad_nib`` → the Bandzugfeder calibrated per source: full width W =
      2·P95 of the pooled measured half-widths (the widest strokes run
      near-perpendicular to the nib edge), edge thickness t = 2·P10 (the
      hairlines run along the edge). The nib ANGLE stays the taught constant
      (Koch 1928: 15° to the horizontal — core/widths.py), never fitted per
      request. Falls back to the documented defaults when nothing is traced.
    - ``constant`` → None (the pooled Gleichzug nib has its own path,
      `pooled_constant_nib`).

    Memoised like the constant nib — see the module docstring.
    """
    if width_resolver not in ("pressure", "broad_nib"):
        return None
    key = (style_id, source_id, width_resolver)
    now = time.monotonic()
    hit = _pen_cache.get(key)
    if hit is not None and now - hit[1] < _NIB_TTL_S:
        return hit[0]
    profiles = await TemplateRepository(db).half_widths_for_source(style_id, source_id)
    pen = pen_from_profiles(width_resolver, profiles)
    _pen_cache[key] = (pen, now)
    return pen


def _invalidate_payloads_for_style(style_id: str) -> None:
    """Drop every memoised render payload of a style.

    Templates hang off the style (not a source), so both invalidation entry
    points clear at style granularity. The `updated_at` component of the key
    already forces a miss after a write — this additionally frees the stale
    entries instead of letting them age out via TTL/eviction.
    """
    for key in [k for k in _payload_cache if k[0] == style_id]:
        _payload_cache.pop(key, None)


def invalidate_pooled_nib(style_id: str, source_id: str) -> None:
    """Drop the memoised nib/pen of one (style, source) pool."""
    _nib_cache.pop((style_id, source_id), None)
    for resolver in ("pressure", "broad_nib"):
        _pen_cache.pop((style_id, source_id, resolver), None)
    _invalidate_payloads_for_style(style_id)


def invalidate_pooled_style(style_id: str) -> None:
    """Drop every memoised nib/pen of a style, across ALL its sources.

    A style can pool from several chart sources (Kurrent: loth-1866 +
    petzendorfer-1889), and a trace/resample/delete issued through source A can
    change a template whose `provenance_source_id` is B — invalidating only
    (style, A) would leave B's pool stale for the TTL. The caches are tiny, so
    the writes simply clear the whole style."""
    for key in [k for k in _nib_cache if k[0] == style_id]:
        _nib_cache.pop(key, None)
    for key in [k for k in _pen_cache if k[0] == style_id]:
        _pen_cache.pop(key, None)
    _invalidate_payloads_for_style(style_id)


@dataclass(frozen=True)
class RenderContext:
    """Everything a render/diagnostic path needs to turn a stored template into
    a payload: the resolved lineature, the style's width resolver, and the two
    mutually-exclusive pooled pens (constant styles get ``nib``, pressure/
    broad-nib styles get ``pen`` — the other stays None)."""

    style_id: str
    style_ratio: list[float]
    slant_deg: float
    width_resolver: str
    nib: float | None  # pooled constant Gleichzug nib (constant styles only)
    pen: PenStyle | None  # pooled Spitz-/Bandzugfeder (pressure/broad_nib only)


async def resolve_render_context(source: Source, db: AsyncSession) -> RenderContext:
    """Resolve the style + the source-pooled pens in one place.

    Consolidates the ``resolve_style`` → constant-nib-if-constant → pooled-pen
    dance every write/template render path used to copy verbatim, so the
    ``constant`` branch lives in exactly one spot. The two pool lookups are
    memoised and mutually exclusive by resolver — one returns None without a
    query — so calling both is cheap regardless of the style.
    """
    style_id, style_ratio, slant_deg, width_resolver = await resolve_style(source, db)
    nib = await pooled_constant_nib(db, style_id, source.id) if width_resolver == "constant" else None
    pen = await pooled_pen(db, style_id, source.id, width_resolver)
    return RenderContext(style_id, style_ratio, slant_deg, width_resolver, nib, pen)


def _pen_fingerprint(pen: PenStyle | None) -> tuple | None:
    """Hashable identity of a pooled pen for the payload cache key.

    `PenStyle`/`BroadNib` are frozen dataclasses and hashable already, but the
    key stays a plain value tuple so no dataclass instance is retained in a
    long-lived key and equality is by calibration values only.
    """
    if pen is None:
        return None
    nib = pen.nib
    nib_fp = None if nib is None else (nib.width_units, nib.angle_deg, nib.edge_fraction)
    return (pen.kind, pen.hairline_half, nib_fp)


def render_payload_cached(glyph_row: dict, glyph_key: str, template_id: int, updated_at, ctx: RenderContext) -> dict:
    """`render_payload_for_template` with the cross-request memo.

    Pure function of (row content, render context) — the key carries the
    template's id + `updated_at` as the row-content proxy plus every render
    input. Returned payloads are SHARED across requests: callers must never
    mutate them (copy before annotating, e.g. ``{**payload, "glyph_key": k}``).
    Synchronous by design — called from the write router's threadpool so a
    miss still computes off the event loop; dict get/set are atomic under the
    GIL, and a rare concurrent double-compute is benign (same value).
    """
    key = (
        ctx.style_id,
        glyph_key,
        template_id,
        None if updated_at is None else str(updated_at),
        ctx.width_resolver,
        tuple(ctx.style_ratio),
        ctx.nib,
        _pen_fingerprint(ctx.pen),
    )
    now = time.monotonic()
    hit = _payload_cache.get(key)
    if hit is not None and now - hit[1] < _NIB_TTL_S:
        return hit[0]
    payload = render_payload_for_template(glyph_row, ctx.style_ratio, ctx.width_resolver, ctx.nib, pen=ctx.pen)
    _payload_cache[key] = (payload, now)
    # Bound the cache: evict in insertion order beyond the cap (plain dict —
    # good enough for a working set of a few dozen templates per style).
    while len(_payload_cache) > _PAYLOAD_CACHE_MAX:
        _payload_cache.pop(next(iter(_payload_cache)))
    return payload
