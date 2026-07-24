"""Public write-path endpoints — the render data the letter/word writer needs.

The public writer used to consume the admin /diagnostic endpoint, which re-runs
the image pipeline (chart load + binarize + skeletonize, ~0.2 s CPU) per request
and ships ~half admin-only overlay ballast. This router serves ONLY the render
subset, straight from the stored template rows — no chart I/O — and sets cache
headers so browser + edge absorb repeat traffic
(docs/proposals/schreibsystem-und-wortbench.md, Phase A). Read-only, no admin
gate — same visibility as /diagnostic.
"""

import unicodedata

import orjson
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import require_db, require_source
from api.http import CACHE_CONTROL
from api.rendering import render_payload_cached, resolve_render_context
from core.compose import compose_word
from core.database import GlyphPairRepository, Source, Template, TemplateRepository
from core.shaping import decompose_ligature_slot, glyph_keys_of, shape_text


router = APIRouter(prefix="/sources/{source_id}/write", tags=["write"])

# A word/sheet needs one entry per UNIQUE glyph key — the full Tafel is ~30,
# the /federprobe input is capped at 48 chars, so 80 bounds any legitimate use.
MAX_BATCH_KEYS = 80

# /word input bound: comfortably above the /federprobe cap (48) and the
# Schriftkunde specimen, small enough to bound compose CPU per request.
MAX_TEXT_LEN = 160


def _template_to_glyph_row(t: Template) -> dict:
    return {
        "anchors": list(t.anchors),
        "half_widths": list(t.half_widths),
        "trace_meta": dict(t.trace_meta or {}),
        "entry": dict(t.entry) if t.entry else {},
        "exit_pt": dict(t.exit_pt) if t.exit_pt else {},
        "advance": t.advance,
    }


def _template_render_entry(t: Template) -> dict:
    """Row dict plus the identity fields the payload memo keys on."""
    return {"row": _template_to_glyph_row(t), "id": t.id, "updated_at": t.updated_at}


def _cached_payload(entry: dict, glyph_key: str, ctx) -> dict:
    """Memoised render payload for one pre-dereferenced template entry.

    The returned dict is SHARED across requests (api.rendering payload cache)
    — callers copy before annotating and never mutate it or its children.
    """
    return render_payload_cached(entry["row"], glyph_key, entry["id"], entry["updated_at"], ctx)


def _geometry_response(content: dict) -> Response:
    """Serialize a render/compose payload with orjson, bypassing FastAPI's
    jsonable_encoder walk — pure overhead over these already-JSON-safe dicts
    of plain floats/lists (~100k numbers per word batch)."""
    return Response(
        content=orjson.dumps(content), media_type="application/json", headers={"Cache-Control": CACHE_CONTROL}
    )


@router.get("/glyphs")
async def get_write_glyphs(
    keys: str = Query(..., description="comma-separated glyph_keys, e.g. 'l,e,longs'"),
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    """Batch render payloads — one round trip for a whole word or Tafel.

    Keys without a canonical land in `missing` instead of failing the batch:
    the client renders what exists and falls back per slot (ligature decompose,
    "not yet curated" notice).
    """
    requested = [k for k in dict.fromkeys(k.strip() for k in keys.split(",")) if k]
    if not requested:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="keys must name at least one glyph_key")
    if len(requested) > MAX_BATCH_KEYS:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"at most {MAX_BATCH_KEYS} keys per request")

    ctx = await resolve_render_context(source, db)
    templates = await TemplateRepository(db).get_many(source.style_id, requested, render_only=True)
    # Dereference the ORM rows into plain dicts ON the event loop — touching a
    # session-bound instance from the threadpool is not thread-safe (an
    # expired/deferred attribute would lazy-load off-loop).
    entries = {t.glyph_key: _template_render_entry(t) for t in templates}
    missing = [k for k in requested if k not in entries]

    # Silhouette/centerline sampling is pure numpy but adds up over ~30 glyphs —
    # keep it off the event loop like the diagnostic does (cache misses only;
    # hits are dict lookups).
    def compute() -> list[dict]:
        out: list[dict] = []
        for key in requested:
            entry = entries.get(key)
            if entry is None:
                continue
            # Shallow copy: the memoised payload is shared across requests.
            out.append({**_cached_payload(entry, key, ctx), "glyph_key": key})
        return out

    glyphs = await run_in_threadpool(compute)
    return _geometry_response({"glyphs": glyphs, "missing": missing})


async def compose_word_payload(text: str, source: Source, db: AsyncSession, *, provenance: bool = False) -> dict:
    """Shape + fetch templates + approved pair overrides + compose ONE text.

    The single server-side word-composition path: /write/word serves it to the
    public writer and the admin specimen-score endpoint re-runs it with
    ``provenance=True`` — so a score always judges exactly the composition the
    writer draws, overrides included. ``text`` is expected pre-normalised.
    """
    ctx = await resolve_render_context(source, db)

    repo = TemplateRepository(db)
    slots = shape_text(text)
    keys = glyph_keys_of(slots)
    entries: dict[str, dict] = {
        t.glyph_key: _template_render_entry(t) for t in await repo.get_many(source.style_id, keys, render_only=True)
    }
    # Ligature fallback (one extra query at most, only when something is missing).
    if any(s.ligature and s.key and s.key not in entries for s in slots):
        expanded = []
        for s in slots:
            if s.ligature and s.key and s.key not in entries:
                expanded.extend(decompose_ligature_slot(s) or [s])
            else:
                expanded.append(s)
        slots = expanded
        keys = glyph_keys_of(slots)
        extra = [k for k in keys if k not in entries]
        for t in await repo.get_many(source.style_id, extra, render_only=True):
            entries[t.glyph_key] = _template_render_entry(t)

    # Approved pair overrides for this text's adjacent joined pairs (redesign
    # R3): one query for the whole word; no rows → the generator path stays
    # byte-identical.
    adjacent: list[tuple[str, str]] = []
    for a, b in zip(slots, slots[1:], strict=False):
        if a.key and b.key and a.joins and b.joins and not a.space and not b.space:
            adjacent.append((a.key, b.key))
    pair_overrides = await GlyphPairRepository(db).approved_for_pairs(source.style_id, adjacent)

    # Render geometry + composition are pure numpy/python — off the event loop.
    # The memoised payloads are shared across requests; compose_word reads
    # them without mutating (pinned by the golden parity fixture).
    def compute() -> dict:
        payloads = {key: (_cached_payload(entries[key], key, ctx) if key in entries else None) for key in keys}
        return compose_word(slots, payloads, pen=ctx.pen, pair_overrides=pair_overrides, provenance=provenance)

    return await run_in_threadpool(compute)


@router.get("/word")
async def get_write_word(
    text: str = Query(..., description="the word or line to write (NFC-normalised, trimmed, ≤160 chars)"),
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    """Compose a whole word/line server-side — ONE cacheable request per text.

    Shaping (long-s rule, closed ligature set, positions), glyph placement and
    the generated Übergänge all run in Python (core.shaping + core.compose, the
    single composition source of truth); the client only animates the returned
    draw items in order. A closed-set ligature without a canonical decomposes
    into its letters server-side, mirroring the old client fallback; whatever
    still has no template lands in ``missing`` and composes as a gap.
    """
    normalized = unicodedata.normalize("NFC", text).strip()
    if not normalized:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail="text must contain at least one non-space character"
        )
    if len(normalized) > MAX_TEXT_LEN:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"text is limited to {MAX_TEXT_LEN} characters"
        )

    composed = await compose_word_payload(normalized, source, db)
    return _geometry_response({"text": normalized, **composed})


@router.get("/glyphs/{glyph_key}")
async def get_write_glyph(
    glyph_key: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    """Render payload for one glyph — 404 when no canonical is traced yet."""
    template = await TemplateRepository(db).get(source.style_id, glyph_key, render_only=True)
    if template is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no canonical for {glyph_key!r}")
    ctx = await resolve_render_context(source, db)
    entry = _template_render_entry(template)
    payload = await run_in_threadpool(_cached_payload, entry, glyph_key, ctx)
    # Shallow copy before annotating — the memoised payload is shared.
    return _geometry_response({**payload, "glyph_key": glyph_key})
