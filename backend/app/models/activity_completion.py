from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, JSON, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ActivityCompletion(Base):
    __tablename__ = "activity_completions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    activity_id: Mapped[int] = mapped_column(
        ForeignKey("activities.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    verified_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    # Evidence/metadata required by the particular activity.
    #
    # Never use this field for sensitive safeguarding case notes.
    evidence: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    staff_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    xp_awarded: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    group_xp_awarded: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    xp_transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("xp_transactions.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    activity: Mapped["Activity"] = relationship(
        "Activity",
        back_populates="completions",
    )

    player: Mapped["Player"] = relationship(
        "Player",
    )

    verified_by: Mapped["User | None"] = relationship(
        "User",
    )

    xp_transaction: Mapped["XPTransaction | None"] = relationship(
        "XPTransaction",
    )
