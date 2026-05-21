"""Canonical endpoints — read existing canonicals + accept stylus traces."""

from fastapi import APIRouter, HTTPException

from api.core.pipeline import canonical_from_path, read_canonical
from api.core.schemas import ResampleRequest, TraceRequest


router = APIRouter(tags=["canonical"])


@router.get("/canonical/{glyph_key}")
async def get_canonical(glyph_key: str) -> dict | None:
    """Return the current canonical JSON for a glyph, or null if not traced yet."""
    return read_canonical(glyph_key)


@router.post("/canonical/{glyph_key}/trace")
async def trace_canonical(glyph_key: str, body: TraceRequest) -> dict:
    """Build a canonical from a user-drawn stylus path.

    Crops the Loth chart by the glyph's bbox (with excludes), runs the M0
    pipeline to get a distance-transform map, samples half-widths along
    the path, normalises to template coords (baseline=0, midband=1), and
    writes mvp/canonical/{glyph_key}_v0.json. The dense input path is
    persisted under _trace.raw_path so callers can re-sample with a
    different n_anchors later (POST /resample).
    """
    if len(body.path) < 2:
        raise HTTPException(status_code=400, detail="stylus path needs at least 2 points")
    raw_path = [{"x": p.x, "y": p.y, "pressure": p.pressure, "t": p.t} for p in body.path]
    try:
        canonical = canonical_from_path(glyph_key, raw_path, n_anchors=body.n_anchors)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return canonical


@router.post("/canonical/{glyph_key}/resample")
async def resample_canonical(glyph_key: str, body: ResampleRequest) -> dict:
    """Re-resample an existing canonical to a different anchor count.

    Reads the stored raw_path from the previous trace and reruns the
    pipeline with a new n_anchors. No new stylus input needed.
    """
    prev = read_canonical(glyph_key)
    if prev is None:
        raise HTTPException(status_code=404, detail=f"no canonical for {glyph_key!r} — draw a stroke first")
    raw_path = prev.get("_trace", {}).get("raw_path")
    if not raw_path:
        raise HTTPException(
            status_code=409,
            detail=f"{glyph_key!r} has no raw_path stored (was traced before raw_path tracking landed) — re-draw to enable resampling",
        )
    try:
        canonical = canonical_from_path(glyph_key, raw_path, n_anchors=body.n_anchors)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return canonical
