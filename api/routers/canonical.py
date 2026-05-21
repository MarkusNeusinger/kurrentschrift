"""Canonical endpoints — read existing canonicals + accept stylus traces."""

from fastapi import APIRouter, HTTPException

from api.core.pipeline import canonical_from_path, read_canonical
from api.core.schemas import TraceRequest


router = APIRouter(tags=["canonical"])


@router.get("/canonical/{glyph_key}")
async def get_canonical(glyph_key: str) -> dict | None:
    """Return the current canonical JSON for a glyph, or null if not traced yet.

    Used by the sidebar to display the ☑ / ☐ status next to each glyph.
    """
    return read_canonical(glyph_key)


@router.post("/canonical/{glyph_key}/trace")
async def trace_canonical(glyph_key: str, body: TraceRequest) -> dict:
    """Build a canonical from a user-drawn stylus path.

    Crops the Loth chart by the glyph's bbox (with excludes), runs the M0
    pipeline to get a distance-transform map, samples half-widths along
    the path, normalises to template coords (baseline=0, midband=1), and
    writes mvp/canonical/{glyph_key}_v0.json. Returns the persisted JSON.
    """
    if len(body.path) < 2:
        raise HTTPException(status_code=400, detail="stylus path needs at least 2 points")
    xy = [(p.x, p.y) for p in body.path]
    pressures = [p.pressure for p in body.path]
    try:
        canonical = canonical_from_path(glyph_key, xy, pressures, n_anchors=body.n_anchors)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return canonical
