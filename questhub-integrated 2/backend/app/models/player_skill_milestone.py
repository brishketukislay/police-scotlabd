from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PlayerSkillMilestone(Base):
    """
    A concrete milestone copied from the skill definition when the
    player starts a skill tree.

    Keeping the values here protects historical records if an admin
    later changes the SkillDefinition.
    """

    __tablename__ = "player_skill_milestones"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    player_skill_id: Mapped[int] = mapped_column(
        ForeignKey("player_skills.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    milestone_key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    required_xp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    reward_id: Mapped[int | None] = mapped_column(
        ForeignKey("rewards.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    completed: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        index=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    validated_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    validation_note: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    player_skill: Mapped["PlayerSkill"] = relationship(
        "PlayerSkill",
        back_populates="milestones",
    )

    reward: Mapped["Reward | None"] = relationship(
        "Reward",
    )

    validated_by: Mapped["User | None"] = relationship(
        "User",
    )
