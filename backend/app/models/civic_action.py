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


class CivicNomination(Base):
    __tablename__ = "civic_nominations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    # Optional target player. A nomination can instead target
    # the whole group.
    player_id: Mapped[int | None] = mapped_column(
        ForeignKey("players.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Public QR tokens are random opaque values.
    #
    # Never expose a database ID as the QR token.
    qr_token: Mapped[str] = mapped_column(
        String(128),
        nullable=False,
        index=True,
    )

    # Submitted by the member of the public.
    #
    # These fields are strictly staff/admin data and must never be
    # returned by player/public leaderboard endpoints.
    submitter_name: Mapped[str | None] = mapped_column(
        String(150),
        nullable=True,
    )

    submitter_organisation: Mapped[str | None] = mapped_column(
        String(200),
        nullable=True,
    )

    submitter_contact: Mapped[str | None] = mapped_column(
        String(250),
        nullable=True,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending",
        index=True,
    )

    # Set once staff accept/reject the nomination.
    reviewed_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    reviewed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    rejection_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    xp_awarded: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    xp_transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("xp_transactions.id", ondelete="SET NULL"),
        nullable=True,
        unique=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
    )

    player: Mapped["Player | None"] = relationship(
        "Player",
    )

    group: Mapped["Group | None"] = relationship(
        "Group",
    )

    programme: Mapped["Programme"] = relationship(
        "Programme",
    )

    reviewed_by: Mapped["User | None"] = relationship(
        "User",
    )

    xp_transaction: Mapped["XPTransaction | None"] = relationship(
        "XPTransaction",
    )


class CivicQRToken(Base):
    __tablename__ = "civic_qr_tokens"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    player_id: Mapped[int | None] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    max_submissions: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    submission_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    programme: Mapped["Programme"] = relationship(
        "Programme",
    )

    player: Mapped["Player | None"] = relationship(
        "Player",
    )

    group: Mapped["Group | None"] = relationship(
        "Group",
    )
