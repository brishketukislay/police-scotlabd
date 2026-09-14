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


class SessionStatus(str, enum.Enum):
    PLANNED = "planned"
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


class YouthSession(Base):
    """
    A scheduled youth-work session.

    Attendance is recorded separately so a player can only receive
    attendance XP once for a particular session.
    """

    __tablename__ = "youth_sessions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    cohort_id: Mapped[int] = mapped_column(
        ForeignKey("cohorts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    phase_id: Mapped[int | None] = mapped_column(
        ForeignKey("phases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    starts_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    ends_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    status: Mapped[SessionStatus] = mapped_column(
        Enum(
            SessionStatus,
            name="session_status",
            native_enum=False,
        ),
        nullable=False,
        default=SessionStatus.PLANNED,
        index=True,
    )

    attendance_xp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=500,
    )

    # How long before/after the session the check-in is valid.
    check_in_window_minutes: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
    )

    check_in_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
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

    programme: Mapped["Programme"] = relationship(
        "Programme",
    )

    cohort: Mapped["Cohort"] = relationship(
        "Cohort",
    )

    phase: Mapped["Phase | None"] = relationship(
        "Phase",
    )

    created_by: Mapped["User | None"] = relationship(
        "User",
    )

    attendance_records: Mapped[list["Attendance"]] = relationship(
        "Attendance",
        back_populates="session",
        cascade="all, delete-orphan",
    )
