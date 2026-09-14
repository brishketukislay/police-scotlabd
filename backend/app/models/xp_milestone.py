from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class XPMilestone(Base):
    __tablename__ = "xp_milestones"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    cohort_id: Mapped[int] = mapped_column(
        ForeignKey("cohorts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    # Example:
    # 500000
    # 1000000
    # 1500000
    threshold_xp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )

    # Optional monetary/non-XP reward.
    reward_id: Mapped[int | None] = mapped_column(
        ForeignKey("rewards.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Visual treatment when the cohort reaches the milestone.
    visual_key: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    # Allows an administrator to disable a milestone without
    # deleting historical configuration.
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
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

    cohort: Mapped["Cohort"] = relationship(
        "Cohort",
    )

    reward: Mapped["Reward | None"] = relationship(
        "Reward",
    )
