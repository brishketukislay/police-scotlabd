from .db.database import (
    DATABASE_URL,
    SessionLocal,
    engine,
    get_db,
    init_db,
)

from .db.base import Base

# Phase 6 compatibility exports.
#
# These imports are intentionally kept here because older routers/services
# may import the XP balance models from app.database.
try:
    from .models import GroupXPBalance, PlayerXPBalance
except ImportError:
    GroupXPBalance = None
    PlayerXPBalance = None


__all__ = [
    "init_db",
    "Base",
    "DATABASE_URL",
    "SessionLocal",
    "engine",
    "get_db",
    "GroupXPBalance",
    "PlayerXPBalance",
]
