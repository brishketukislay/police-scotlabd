from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PlayerSkillStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class PlayerSkill(Base):
    """
    An instance of a configured skill tree assigned to a player.

    SkillDefinition = template.
    PlayerSkill = the player's actual journey through that template.
    """

    __tablename__ = "player_skills"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    skill_definition_id: Mapped[int] = mapped_column(
        ForeignKey("skill_definitions.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status: Mapped[PlayerSkillStatus] = mapped_column(
        Enum(
            PlayerSkillStatus,
            name="player_skill_status",
            native_enum=False,
        ),
        nullable=False,
        default=PlayerSkillStatus.ACTIVE,
        index=True,
    )

    # The currently active milestone.
    current_milestone_key: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Lifetime skill-tree sequence for this player.
    #
    # 1 = first completed tree
    # 2 = second completed tree, etc.
    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    assigned_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
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

    abandoned_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    player: Mapped["Player"] = relationship(
        "Player",
    )

    skill_definition: Mapped["SkillDefinition"] = relationship(
        "SkillDefinition",
    )

    assigned_by: Mapped["User | None"] = relationship(
        "User",
    )

    milestones: Mapped[list["PlayerSkillMilestone"]] = relationship(
        "PlayerSkillMilestone",
        back_populates="player_skill",
        cascade="all, delete-orphan",
        order_by="PlayerSkillMilestone.position",
    )
