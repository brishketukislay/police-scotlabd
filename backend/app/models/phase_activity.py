from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PhaseActivity(Base):
    """
    A configured activity belonging to a phase.

    Activity types can include:
        session
        reflection
        challenge
        visit
        workshop
        skill_choice
        digital_bystander
    """

    __tablename__ = "phase_activities"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    phase_id: Mapped[int] = mapped_column(
        ForeignKey("phases.id", ondelete="CASCADE"),
        nullable=False,
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

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    required: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    # Frontend/activity-specific configuration.
    config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Allows an activity to award/configure XP without putting
    # point values into frontend code.
    xp_config: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    ends_at: Mapped[datetime | None] = mapped_column(
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

    phase: Mapped["Phase"] = relationship(
        "Phase",
        back_populates="activities",
    )
