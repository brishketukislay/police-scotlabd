from __future__ import annotations

from typing import Callable

from fastapi import Depends, HTTPException, status

from .auth import get_current_user
from .db.models import User


PLAYER = "player"
YOUTH_WORKER = "youth_worker"
ADMIN = "admin"

STAFF_ROLES = {
    YOUTH_WORKER,
    ADMIN,
}


def require_role(*roles: str) -> Callable:
    """
    Require the authenticated user to have one of the supplied roles.
    """

    allowed = set(roles)

    def dependency(
        user: User = Depends(get_current_user),
    ) -> User:
        if user.role not in allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions.",
            )

        return user

    return dependency


def require_staff(
    user: User = Depends(get_current_user),
) -> User:
    """
    Youth workers and admins.
    """

    if user.role not in STAFF_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Staff access required.",
        )

    return user


def require_player(
    user: User = Depends(get_current_user),
) -> User:
    """
    Player-only endpoint dependency.
    """

    if user.role != PLAYER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Player access required.",
        )

    return user
