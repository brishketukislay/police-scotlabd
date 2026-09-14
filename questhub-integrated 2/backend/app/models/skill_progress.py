from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class SkillTreeProgress(Base):
    __tablename__ = "skill_tree_progress"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    skill_tree_id: Mapped[int] = mapped_column(
        ForeignKey("skill_trees.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # A player can repeat the same skill tree later.
    # This identifies the individual run of that tree.
    cycle_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    current_milestone: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="active",
        index=True,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    player: Mapped["Player"] = relationship(
        "Player",
    )

    skill_tree: Mapped["SkillTree"] = relationship(
        "SkillTree",
    )
