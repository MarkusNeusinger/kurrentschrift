"""Word-sample endpoints — the connected-writing specimens of a source.

Public reads over the `words.json` sidecar next to the chart raster (see
`core.chart.load_word_samples`): the admin word-comparison view lists the
specimens and loads each crop via a plain `<img>` tag, which cannot send the
admin header — same reasoning as the public bbox crops in `chart.py`. The
plates are PD source bytes, so nothing here is secret; responses are cached
like the other public reads (the sidecar only changes with a deploy).
"""

import logging
import unicodedata

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db, require_source
from api.http import CACHE_CONTROL
from api.rendering import resolve_render_context
from api.routers.write import compose_word_payload
from api.schemas import WordSampleOut
from core.chart import load_word_samples, word_sample_crop_to_png_bytes
from core.database import Source
from core.word_metric import score_word, score_word_segments, skeleton_for_sample


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/sources/{source_id}", tags=["word-samples"])


def _to_out(sample: dict) -> WordSampleOut:
    y0, y1 = int(sample["y0"]), int(sample["y1"])
    x0, x1 = int(sample["x0"]), int(sample["x1"])
    # An empty/whitespace set tag (hand-maintained data) must not classify the
    # row as another hand — normalize to None.
    sample_set = str(sample.get("set") or "").strip() or None
    return WordSampleOut(
        id=sample["id"],
        word=str(sample["word"]),
        kind="pair" if sample.get("kind") == "pair" else "word",
        sample_set=sample_set,
        width=x1 - x0,
        height=y1 - y0,
        baseline_y=int(sample["baseline_y"]) - y0,
        midband_y=int(sample["midband_y"]) - y0,
    )


@router.get("/word-samples", response_model=list[WordSampleOut])
async def list_word_samples(response: Response, source: Source = Depends(require_source)) -> list[WordSampleOut]:
    """All specimens of the source; `[]` when it has no sidecar (most sources)."""
    samples = await run_in_threadpool(load_word_samples, source.chart_path)
    response.headers["Cache-Control"] = CACHE_CONTROL
    return [_to_out(s) for s in samples]


@router.get("/word-samples/{sample_id}/crop")
async def get_word_sample_crop(sample_id: str, source: Source = Depends(require_source)) -> Response:
    """One specimen crop as grayscale PNG, exclude rects painted paper-white."""

    # Sidecar read + plate decode + crop are file/CPU-bound — keep them off the
    # event loop like the chart crops do. A missing/corrupt plate or an
    # out-of-plate rect is hand-maintained-data breakage, not a server fault:
    # answer 404, don't 500 the public read.
    def compute() -> bytes | None:
        samples = load_word_samples(source.chart_path)
        sample = next((s for s in samples if s["id"] == sample_id), None)
        if sample is None:
            return None
        try:
            return word_sample_crop_to_png_bytes(source.chart_path, sample)
        except (OSError, ValueError):
            logger.warning("word sample crop failed for %r on source %r", sample_id, source.id)
            return None

    png = await run_in_threadpool(compute)
    if png is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"word sample {sample_id!r} not found")
    return Response(content=png, media_type="image/png", headers={"Cache-Control": CACHE_CONTROL})


@router.get("/word-samples/{sample_id}/score", dependencies=[Depends(require_admin)])
async def get_word_sample_score(
    sample_id: str, source: Source = Depends(require_source), db: AsyncSession = Depends(require_db)
):
    """Score the CURRENT composition of one specimen against its plate ink.

    Admin-only (redesign R1b Stufe 2): runs the frozen wordbench ruler
    (`core.word_metric`, the exact metric the bench freezes) on the same
    composition `/write/word` serves — approved pair overrides included — so
    the admin word comparison can rank where optimisation is still needed.
    Per-segment attribution rows (compose provenance) point at the letter or
    join that carries the penalty. Uncached: the score moves with every
    template/pair write.
    """
    samples = await run_in_threadpool(load_word_samples, source.chart_path)
    sample = next((s for s in samples if s["id"] == sample_id), None)
    if sample is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"word sample {sample_id!r} not found")

    normalized = unicodedata.normalize("NFC", str(sample["word"])).strip()
    composed = await compose_word_payload(normalized, source, db, provenance=True)
    ctx = await resolve_render_context(source, db)

    # Skeletonising the plate crop is the expensive part (~0.2 s cold, then
    # cached per sample — the plates are immutable per deploy); scoring itself
    # is a small grid search. All CPU-bound → off the event loop.
    def compute() -> dict | None:
        try:
            skel = skeleton_for_sample(source.chart_path, sample)
        except (OSError, ValueError):
            logger.warning("word sample score failed for %r on source %r", sample_id, source.id)
            return None
        word_meta = {
            "rect": [int(sample["x0"]), int(sample["y0"]), int(sample["x1"]), int(sample["y1"])],
            "baseline_y": int(sample["baseline_y"]),
            "midband_y": int(sample["midband_y"]),
        }
        report = score_word(composed, word_meta, skel, ctx.nib)
        report["segments"] = (
            [] if report["failed"] else score_word_segments(composed, word_meta, skel, ctx.nib, report["registration"])
        )
        return report

    report = await run_in_threadpool(compute)
    if report is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"word sample {sample_id!r} not found")
    return {"id": sample_id, "word": normalized, **report}
