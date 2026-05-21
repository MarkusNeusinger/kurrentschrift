"""Render endpoints — wrap the CLI render helpers so the web UI can
display the side-by-side review without the user dropping to a terminal.

Implementation just calls into mvp.render_canonicals.main() which writes
mvp/out/canonicals-phase-a.png; we then stream that file back. Matplotlib
plus skimage take a second or two, so the endpoint is GET with a
cache-busting query param expected from the frontend (e.g. ?t=<epoch_ms>)
to force a re-render after canonical edits.
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from api.core.settings import settings
from mvp import render_canonicals


router = APIRouter(tags=["render"])


@router.get("/render/canonicals")
async def get_canonicals_render():
    """Re-render the 3x3 review PNG (canonical / Loth+skeleton+anchors / Loth pure)."""
    try:
        render_canonicals.main()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"render failed: {exc}") from exc
    out_path = settings.repo_root / "mvp" / "out" / "canonicals-phase-a.png"
    if not out_path.exists():
        raise HTTPException(status_code=500, detail="render produced no output")
    return FileResponse(out_path, media_type="image/png")
