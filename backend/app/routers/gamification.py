from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..db.database import get_db
from ..db.models import (
    Player,
    YouthGroup,
    XPTransaction,
)
from ..services.gamification import (
    get_active_programme,
    get_programme_xp,
    get_high_risers,
)


router = APIRouter(
    prefix="/api/gamification",
    tags=["gamification"],
)


@router.get("/leaderboards")
def leaderboards(
    db: Session = Depends(get_db),
):
    programme = get_active_programme(db)

    overall_rows = (
        db.query(
            Player.id,
            Player.gamertag,
            Player.avatar,
            func.coalesce(
                func.sum(XPTransaction.amount),
                0,
            ).label("xp"),
        )
        .join(
            YouthGroup,
            YouthGroup.id == Player.group_id,
        )
        .outerjoin(
            XPTransaction,
            XPTransaction.player_id == Player.id,
        )
        .filter(
            YouthGroup.programme_id == programme.id,
            Player.active.is_(True),
            Player.public_visible.is_(True),
        )
        .group_by(
            Player.id,
            Player.gamertag,
            Player.avatar,
        )
        .order_by(
            func.sum(XPTransaction.amount).desc()
        )
        .all()
    )

    return {
        "programme": {
            "id": programme.id,
            "name": programme.name,
            "target_xp": programme.target_xp,
            "group_xp": get_programme_xp(
                db,
                programme.id,
            ),
        },
        "overall": [
            {
                "rank": index + 1,
                "gamertag": row.gamertag,
                "avatar": row.avatar,
                "xp": int(row.xp or 0),
            }
            for index, row in enumerate(overall_rows)
        ],
        "high_risers": get_high_risers(
            db,
            programme.id,
            days=7,
            limit=10,
        ),
    }


@router.get("/programme")
def programme_progress(
    db: Session = Depends(get_db),
):
    programme = get_active_programme(db)

    current = get_programme_xp(
        db,
        programme.id,
    )

    target = int(
        programme.target_xp
        or 1_500_000
    )

    return {
        "current_xp": current,
        "target_xp": target,
        "percentage": round(
            min(
                100,
                (current / target) * 100,
            ),
            2,
        ),
        "remaining_xp": max(
            0,
            target - current,
        ),
        "milestones": [
            {
                "xp": 500_000,
                "label": "Level 1",
                "reward": "£250",
                "unlocked": current >= 500_000,
            },
            {
                "xp": 1_000_000,
                "label": "Level 2",
                "reward": "£750",
                "unlocked": current >= 1_000_000,
            },
            {
                "xp": 1_500_000,
                "label": "Grand Finale",
                "reward": "£2,200",
                "unlocked": current >= 1_500_000,
            },
        ],
    }