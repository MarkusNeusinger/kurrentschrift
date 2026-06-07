"""Hand (writer) endpoints — read-only list + get. Thin until the import pipeline."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import require_db
from api.schemas import HandOut
from core.database import Hand, HandRepository


router = APIRouter(prefix="/hands", tags=["hands"])


def _to_out(hand: Hand) -> HandOut:
    return HandOut(id=hand.id, style_id=hand.style_id, label=hand.label, era=hand.era, note=hand.note)


@router.get("", response_model=list[HandOut])
async def list_hands(db: AsyncSession = Depends(require_db)) -> list[HandOut]:
    return [_to_out(h) for h in await HandRepository(db).list()]


@router.get("/{hand_id}", response_model=HandOut)
async def get_hand(hand_id: str, db: AsyncSession = Depends(require_db)) -> HandOut:
    hand = await HandRepository(db).get(hand_id)
    if hand is None:
        raise HTTPException(404, detail=f"hand {hand_id!r} not found")
    return _to_out(hand)
