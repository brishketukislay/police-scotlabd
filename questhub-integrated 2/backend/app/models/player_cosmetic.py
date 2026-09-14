from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PlayerCosmetic(Base):
    """
    A cosmetic unlocked by a player.
    """

    __tablename__ = "player_cosmetics"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    cosmetic_id: Mapped[int] = mapped_column(
        ForeignKey("cosmetics.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    equipped: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    # The event which unlocked it.
    source_type: Mapped[str | None] = mapped_column(
        nullable=True,
    )

    source_id: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    player: Mapped["Player"] = relationship(
        "Player",
    )

    cosmetic: Mapped["Cosmetic"] = relationship(
        "Cosmetic",
        back_populates="player_cosmetics",
    )
