from __future__ import annotations

from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from .auth import get_current_user
from .db.database import get_db
from .db.models import Player, User


def get_current_player(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> Player:
    """
    Resolve the authenticated User to their Player record.

    The client never supplies player_id for player-owned operations.
    """

    if user.role != "player":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Player access required.",
        )

    player = (
        db.query(Player)
        .filter(
            Player.user_id == user.id,
            Player.active.is_(True),
        )
        .first()
    )

    if player is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player profile not found.",
        )

    if player.suspended:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Player account is suspended.",
        )

    return player
