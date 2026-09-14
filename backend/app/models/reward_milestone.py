from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class MilestoneScope(str, enum.Enum):
    PLAYER = "player"
    GROUP = "group"


class RewardMilestone(Base):
    """
    Threshold that activates a reward.

    Example:

        group + 500,000 XP -> £250
        player + 15,000 XP -> mystery reward
    """

    __tablename__ = "reward_milestones"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    reward_id: Mapped[int] = mapped_column(
        ForeignKey("rewards.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    scope: Mapped[MilestoneScope] = mapped_column(
        Enum(
            MilestoneScope,
            name="milestone_scope",
            native_enum=False,
        ),
        nullable=False,
        index=True,
    )

    threshold_xp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    # Whether this milestone can trigger once per player,
    # once per programme, or repeatedly.
    repeatable: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
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

    programme: Mapped["Programme"] = relationship(
        "Programme",
    )

    reward: Mapped["Reward"] = relationship(
        "Reward",
        back_populates="milestones",
    )

    claims: Mapped[list["RewardClaim"]] = relationship(
        "RewardClaim",
        back_populates="milestone",
    )
