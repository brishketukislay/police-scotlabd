from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PlayerBadge(Base):
    """
    Immutable-ish achievement record.

    Once earned, the badge remains part of the player's history.
    """

    __tablename__ = "player_badges"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    badge_id: Mapped[int] = mapped_column(
        ForeignKey("badges.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    skill_tree_id: Mapped[int | None] = mapped_column(
        ForeignKey("skill_trees.id", ondelete="SET NULL"),
        nullable=True,
    )

    earned_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    player: Mapped["Player"] = relationship(
        "Player",
    )

    badge: Mapped["Badge"] = relationship(
        "Badge",
    )

    skill_tree: Mapped["SkillTree | None"] = relationship(
        "SkillTree",
    )
