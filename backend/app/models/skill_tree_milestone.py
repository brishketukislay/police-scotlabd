from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class SkillTreeMilestone(Base):
    """
    A concrete step in a skill tree.

    The three-milestone structure is configurable rather than hard-coded,
    although the initial programme can seed three milestones.
    """

    __tablename__ = "skill_tree_milestones"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    skill_tree_id: Mapped[int] = mapped_column(
        ForeignKey("skill_trees.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    xp_required: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    xp_reward: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    # Prevents the same milestone reward from being processed twice.
    reward_processed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
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

    skill_tree: Mapped["SkillTree"] = relationship(
        "SkillTree",
        back_populates="milestones",
    )
