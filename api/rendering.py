"""Style resolution + source-pooled nib, shared by the templates and write routers.

The pooled constant nib (architektur.md §5: one Gleichzug pen per source) is an
O(all-templates) JSONB scan whose result only changes when a template of the
source is written — memoise it per (style, source) with explicit invalidation
from the admin write endpoints. Single-process cache by design: the service
runs one instance (max-instances=1) and every template write flows through this
process; the TTL is the safety net for out-of-band writes (psql, migrations).
"""

import statistics
import time

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from core.database import Source, StyleRepository, TemplateRepository
from core.widths import BroadNib, PenStyle


_NIB_TTL_S = 600.0
# (style_id, source_id) -> (pooled nib radius in x-height units or None, computed_at)
_nib_cache: dict[tuple[str, str], tuple[float | None, float]] = {}
# (style_id, source_id, width_resolver) -> (PenStyle or None, computed_at)
_pen_cache: dict[tuple[str, str, str], tuple[PenStyle | None, float]] = {}


async def resolve_style(source: Source, db: AsyncSession) -> tuple[str, list[float], float, str]:
    """Return (style_id, resolved style_ratio, resolved slant_deg, width_resolver) for a source.

    A source may override ratio/slant per chart (null => use the style); the
    width resolver is a pure style property a source can never override
    (architektur.md §5).
    """
    style = await StyleRepository(db).get(source.style_id)
    if style is None:
        raise HTTPException(500, detail=f"source {source.id!r} references unknown style {source.style_id!r}")
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


def invalidate_pooled_nib(style_id: str, source_id: str) -> None:
    """Drop the memoised nib/pen after a template write (trace/resample/delete)."""
    _nib_cache.pop((style_id, source_id), None)
    for resolver in ("pressure", "broad_nib"):
        _pen_cache.pop((style_id, source_id, resolver), None)
