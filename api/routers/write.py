"""Public write-path endpoints — the render data the letter/word writer needs.

The public writer used to consume the admin /diagnostic endpoint, which re-runs
the image pipeline (chart load + binarize + skeletonize, ~0.2 s CPU) per request
and ships ~half admin-only overlay ballast. This router serves ONLY the render
subset, straight from the stored template rows — no chart I/O — and sets cache
headers so browser + edge absorb repeat traffic
(docs/proposals/schreibsystem-und-wortbench.md, Phase A). Read-only, no admin
gate — same visibility as /diagnostic.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import require_db, require_source
from api.rendering import pooled_constant_nib, resolve_style
from core.database import Source, Template, TemplateRepository
from core.pipeline import render_payload_for_template


router = APIRouter(prefix="/sources/{source_id}/write", tags=["write"])

# Template geometry only changes on an admin re-trace; five minutes of browser
# staleness is fine for the public pages while the admin surfaces keep reading
# the uncached /diagnostic. `s-maxage` targets the CDN once a cache rule allows
# JSON on write/*; stale-while-revalidate bridges revalidation without a
# blocking round trip.
CACHE_CONTROL = "public, max-age=300, s-maxage=86400, stale-while-revalidate=604800"

# A word/sheet needs one entry per UNIQUE glyph key — the full Tafel is ~30,
# the /federprobe input is capped at 48 chars, so 80 bounds any legitimate use.
MAX_BATCH_KEYS = 80


def _template_to_glyph_row(t: Template) -> dict:
    return {
        "anchors": list(t.anchors),
        "half_widths": list(t.half_widths),
        "trace_meta": dict(t.trace_meta or {}),
        "entry": dict(t.entry) if t.entry else {},
        "exit_pt": dict(t.exit_pt) if t.exit_pt else {},
        "advance": t.advance,
    }


@router.get("/glyphs")
async def get_write_glyphs(
    response: Response,
    keys: str = Query(..., description="comma-separated glyph_keys, e.g. 'l-initial,e-medial'"),
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    """Batch render payloads — one round trip for a whole word or Tafel.

    Keys without a canonical land in `missing` instead of failing the batch:
    the client renders what exists and falls back per slot (ligature decompose,
    "Noch nicht kuratiert" notice).
    """
    requested = [k for k in dict.fromkeys(k.strip() for k in keys.split(",")) if k]
    if not requested:
        raise HTTPException(422, detail="keys must name at least one glyph_key")
    if len(requested) > MAX_BATCH_KEYS:
        raise HTTPException(422, detail=f"at most {MAX_BATCH_KEYS} keys per request")

    style_id, style_ratio, _slant, width_resolver = await resolve_style(source, db)
    nib = await pooled_constant_nib(db, style_id, source.id) if width_resolver == "constant" else None
    templates = await TemplateRepository(db).get_many(source.style_id, requested)
    by_key = {t.glyph_key: t for t in templates}
    missing = [k for k in requested if k not in by_key]

    # Silhouette/centerline sampling is pure numpy but adds up over ~30 glyphs —
    # keep it off the event loop like the diagnostic does.
    def compute() -> list[dict]:
        out: list[dict] = []
        for key in requested:
            t = by_key.get(key)
            if t is None:
                continue
            payload = render_payload_for_template(_template_to_glyph_row(t), style_ratio, width_resolver, nib)
            payload["glyph_key"] = key
            out.append(payload)
        return out

    glyphs = await run_in_threadpool(compute)
    response.headers["Cache-Control"] = CACHE_CONTROL
    return {"glyphs": glyphs, "missing": missing}


@router.get("/glyphs/{glyph_key}")
async def get_write_glyph(
    glyph_key: str, response: Response, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    """Render payload for one glyph — 404 when no canonical is traced yet."""
    template = await TemplateRepository(db).get(source.style_id, glyph_key)
    if template is None:
        raise HTTPException(404, detail=f"no canonical for {glyph_key!r}")
    style_id, style_ratio, _slant, width_resolver = await resolve_style(source, db)
    nib = await pooled_constant_nib(db, style_id, source.id) if width_resolver == "constant" else None
    payload = await run_in_threadpool(
        render_payload_for_template, _template_to_glyph_row(template), style_ratio, width_resolver, nib
    )
    payload["glyph_key"] = glyph_key
    response.headers["Cache-Control"] = CACHE_CONTROL
    return payload
