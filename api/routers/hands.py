"""Hand (writer) endpoints — read-only list + get.

Admin-gated since 2026-08-28: the hands table is the writer registry of the
statistics layer (H1/H2 aggregates, the own-hand capture chain), i.e. the
index of the reserved dataset (quellen-und-rechte.md §5). No public page ever
read it — the public renders are pinned to the site-wide source, never to a
hand — so the only consumers are the workbench and the snapshot tool, which
carry the admin token.
"""

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth import require_admin
from api.dependencies import require_db
from api.http import NO_STORE
from api.schemas import HandOut
from core.database import Hand, HandRepository


router = APIRouter(prefix="/hands", tags=["hands"], dependencies=[Depends(require_admin)])


def _to_out(hand: Hand) -> HandOut:
    return HandOut(id=hand.id, style_id=hand.style_id, label=hand.label, era=hand.era, note=hand.note)


@router.get("", response_model=list[HandOut])
async def list_hands(response: Response, db: AsyncSession = Depends(require_db)) -> list[HandOut]:
    # A gated read must never land in a shared cache (api/http.py).
    response.headers["Cache-Control"] = NO_STORE
    return [_to_out(h) for h in await HandRepository(db).list()]


@router.get("/{hand_id}", response_model=HandOut)
async def get_hand(hand_id: str, response: Response, db: AsyncSession = Depends(require_db)) -> HandOut:
    hand = await HandRepository(db).get(hand_id)
    if hand is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"hand {hand_id!r} not found")
    response.headers["Cache-Control"] = NO_STORE
    return _to_out(hand)
