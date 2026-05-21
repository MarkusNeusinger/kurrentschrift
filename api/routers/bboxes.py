"""Bbox endpoints — read/write loth_bboxes.json."""

from fastapi import APIRouter, HTTPException

from api.core.pipeline import read_bboxes_file, write_bboxes_file
from api.core.schemas import GlyphBbox
from api.core.settings import settings


router = APIRouter(tags=["bboxes"])


@router.get("/bboxes")
async def get_bboxes() -> dict:
    """Full content of loth_bboxes.json — returned verbatim.

    Returned shape matches the file: `{_note, image_size, bboxes: {key: dict|null}}`.
    The frontend reads `bboxes` directly; `image_size` lets it set the canvas.
    """
    return read_bboxes_file(settings.bboxes_json)


@router.put("/bboxes/{glyph_key}")
async def put_bbox(glyph_key: str, bbox: GlyphBbox) -> dict:
    """Upsert one glyph's bbox + calibration + excludes into loth_bboxes.json.

    Returns the persisted entry. The request body must be a complete
    GlyphBbox — partial updates aren't supported (frontend always has the
    full state for the selected glyph).
    """
    data = read_bboxes_file(settings.bboxes_json)
    if glyph_key not in data.get("bboxes", {}):
        raise HTTPException(status_code=404, detail=f"unknown glyph_key {glyph_key!r}")
    entry = bbox.model_dump(exclude_none=True)
    # Tuples (start_xy) become lists in JSON — normalise for consistency with manual edits.
    if "start_xy" in entry and isinstance(entry["start_xy"], tuple):
        entry["start_xy"] = list(entry["start_xy"])
    data["bboxes"][glyph_key] = entry
    write_bboxes_file(settings.bboxes_json, data)
    return entry
