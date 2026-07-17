"""Word-sample endpoints — the connected-writing specimens of a source.

Public reads over the `words.json` sidecar next to the chart raster (see
`core.chart.load_word_samples`): the admin word-comparison view lists the
specimens and loads each crop via a plain `<img>` tag, which cannot send the
admin header — same reasoning as the public bbox crops in `chart.py`. The
plates are PD source bytes, so nothing here is secret; responses are cached
like the other public reads (the sidecar only changes with a deploy).
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.concurrency import run_in_threadpool

from api.dependencies import require_source
from api.http import CACHE_CONTROL
from api.schemas import WordSampleOut
from core.chart import load_word_samples, word_sample_crop_to_png_bytes
from core.database import Source


router = APIRouter(prefix="/sources/{source_id}", tags=["word-samples"])


def _to_out(sample: dict) -> WordSampleOut:
    y0, y1 = int(sample["y0"]), int(sample["y1"])
    x0, x1 = int(sample["x0"]), int(sample["x1"])
    return WordSampleOut(
        id=sample["id"],
        word=str(sample["word"]),
        kind="pair" if sample.get("kind") == "pair" else "word",
        sample_set=sample.get("set"),
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
    # event loop like the chart crops do.
    def compute() -> bytes | None:
        samples = load_word_samples(source.chart_path)
        sample = next((s for s in samples if s["id"] == sample_id), None)
        if sample is None:
            return None
        return word_sample_crop_to_png_bytes(source.chart_path, sample)

    png = await run_in_threadpool(compute)
    if png is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"word sample {sample_id!r} not found")
    return Response(content=png, media_type="image/png", headers={"Cache-Control": CACHE_CONTROL})
