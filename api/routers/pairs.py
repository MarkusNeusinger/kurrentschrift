"""Glyph-pair override endpoints (redesign R3, proposal B).

Sparse per-pair overrides over the §4 join generator: reads are public (the
admin pair matrix badges overridden joins via a plain fetch), writes are
admin-gated like the template writes. The composer consumes ONLY approved
rows (see `GlyphPairRepository.approved_for_pairs` in the word endpoint);
storing an unapproved harvest is safe.
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db, require_source
from api.schemas import GlyphPairIn, GlyphPairOut
from core.database import GlyphPair, GlyphPairRepository, Source
from core.shaping import is_registry_glyph_key


router = APIRouter(prefix="/sources/{source_id}/pairs", tags=["pairs"])


def _to_out(row: GlyphPair) -> GlyphPairOut:
    return GlyphPairOut(
        left_key=row.left_key,
        right_key=row.right_key,
        variant=row.variant,
        geometry=row.geometry,
        provenance=row.provenance,
        provenance_source_id=row.provenance_source_id,
        specimen_id=row.specimen_id,
        approved=bool(row.approved),
    )


def _reject_unknown_keys(left_key: str, right_key: str) -> None:
    """Both sides must be registry glyphs — a typo'd key would store fine but
    never match a shaped pair, silently doing nothing."""
    for key in (left_key, right_key):
        if not is_registry_glyph_key(key):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"glyph_key {key!r} is not a registry glyph"
            )


@router.get("", response_model=list[GlyphPairOut])
async def list_pairs(
    request: Request,
    all: bool = False,
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    """List pair overrides. Public callers see APPROVED rows only (matching
    what actually renders); `?all=true` additionally returns unreviewed rows
    — e.g. a fresh bulk harvest — and is admin-gated so unapproved data never
    leaks to public consumers or bloats their responses.

    Deliberately uncached like /templates: the admin edits and expects fresh
    rows immediately."""
    if all:
        # Conditional gate: the dependency is a plain callable over the two
        # auth headers — invoked manually because it only applies to ?all=true.
        require_admin(
            x_admin_token=request.headers.get("X-Admin-Token"),
            cf_access_jwt=request.headers.get("Cf-Access-Jwt-Assertion"),
        )
    rows = await GlyphPairRepository(db).list(source.style_id)
    return [_to_out(r) for r in rows if all or r.approved]


@router.get("/{left_key}/{right_key}", response_model=GlyphPairOut)
async def get_pair(
    request: Request,
    left_key: str,
    right_key: str,
    variant: int = 0,
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    row = await GlyphPairRepository(db).get(source.style_id, left_key, right_key, variant=variant)
    if row is not None and not row.approved:
        # Unapproved rows are admin work-in-progress — same contract as the
        # list endpoint: they never leak to public callers (404, not 401, so
        # existence isn't revealed either).
        try:
            require_admin(
                x_admin_token=request.headers.get("X-Admin-Token"),
                cf_access_jwt=request.headers.get("Cf-Access-Jwt-Assertion"),
            )
        except HTTPException:
            row = None
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no pair override for {left_key!r}→{right_key!r}")
    return _to_out(row)


@router.put("/{left_key}/{right_key}", response_model=GlyphPairOut, dependencies=[Depends(require_admin)])
async def put_pair(
    left_key: str,
    right_key: str,
    payload: GlyphPairIn,
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    _reject_unknown_keys(left_key, right_key)
    row = await GlyphPairRepository(db).upsert(
        source.style_id,
        left_key,
        right_key,
        variant=payload.variant,
        geometry=payload.geometry.model_dump(),
        provenance=payload.provenance,
        # The specimen pointer belongs to harvested rows only — an authored
        # (freehand) override has no source specimen to cite.
        provenance_source_id=source.id if payload.provenance == "harvested" else None,
        specimen_id=payload.specimen_id if payload.provenance == "harvested" else None,
        approved=payload.approved,
    )
    return _to_out(row)


@router.delete("/{left_key}/{right_key}", status_code=204, dependencies=[Depends(require_admin)])
async def delete_pair(
    left_key: str,
    right_key: str,
    variant: int = 0,
    source: Source = Depends(require_source),
    db: AsyncSession = Depends(require_db),
):
    deleted = await GlyphPairRepository(db).delete(source.style_id, left_key, right_key, variant=variant)
    if not deleted:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"no pair override for {left_key!r}→{right_key!r}")
