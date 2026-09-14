from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


class GameEvent(Base):
    """
    Immutable record of something that happened in the game.

    Events are intentionally generic.

    Examples:

        attendance.completed
        reflection.completed
        challenge.completed
        skill.milestone_completed
        staff.xp_awarded
        community_award.approved

    The event itself does not contain XP values.

    XP is calculated by PointRule records so that programme
    administrators can change the game economy without changing code.
    """

    __tablename__ = "game_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    phase_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("phases.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    player_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("players.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    payload: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    idempotency_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    occurred_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    programme = relationship(
        "Programme",
    )

    phase = relationship(
        "Phase",
    )

    player = relationship(
        "Player",
    )

    group = relationship(
        "YouthGroup",
    )

    created_by_user = relationship(
        "User",
    )

    __table_args__ = (
        Index(
            "ix_game_events_programme_type_occurred",
            "programme_id",
            "event_type",
            "occurred_at",
        ),
        UniqueConstraint(
            "programme_id",
            "idempotency_key",
            name="uq_game_event_programme_idempotency",
        ),
    )
