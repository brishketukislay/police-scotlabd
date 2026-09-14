from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..db.database import get_db
from ..db.models import Player, XPTransaction

router = APIRouter(prefix="/api/leaderboard", tags=["leaderboard"])


@router.get("")
def leaderboard(db: Session = Depends(get_db)):
    rows = (
        db.query(
            Player.id,
            Player.gamertag,
            Player.avatar,
            func.coalesce(func.sum(XPTransaction.amount), 0).label("xp"),
        )
        .outerjoin(XPTransaction, XPTransaction.player_id == Player.id)
        .filter(Player.active == True)
        .group_by(Player.id)
        .order_by(func.sum(XPTransaction.amount).desc())
        .all()
    )

    return [
        {
            "rank": index + 1,
            "gamertag": row.gamertag,
            "avatar": row.avatar,
            "xp": int(row.xp or 0),
        }
        for index, row in enumerate(rows)
    ]
