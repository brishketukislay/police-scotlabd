from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Activity(Base):
    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    phase_id: Mapped[int | None] = mapped_column(
        ForeignKey("phases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    activity_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    # Examples:
    # attendance
    # reflection
    # behaviour
    # restorative
    # staff_award
    # team_activity
    # skill_validation
    verification_mode: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="staff",
    )

    xp_reward: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    group_xp_reward: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Additional configurable rules for the activity.
    #
    # Example:
    # {
    #   "max_completions_per_day": 1,
    #   "requires_staff_note": true
    # }
    rules: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
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

    phase: Mapped["Phase | None"] = relationship(
        "Phase",
    )

    completions: Mapped[list["ActivityCompletion"]] = relationship(
        "ActivityCompletion",
        back_populates="activity",
        cascade="all, delete-orphan",
    )
