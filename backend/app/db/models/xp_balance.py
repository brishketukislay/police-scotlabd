from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .core import Base, Player, Programme


class PlayerXPBalance(Base):
    """
    Materialised current/lifetime XP balance for a player.

    XPTransaction remains the source-of-truth ledger.
    This table is the fast-read projection.
    """

    __tablename__ = "player_xp_balances"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    current_xp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    lifetime_xp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    lifetime_xp_removed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    player: Mapped[Player] = relationship(
        "Player",
    )


class GroupXPBalance(Base):
    """
    Materialised programme-wide collective XP balance.

    The balance belongs to the programme, not an individual youth group.
    """

    __tablename__ = "group_xp_balances"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    current_xp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    lifetime_xp_awarded: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    lifetime_xp_removed: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    programme: Mapped[Programme] = relationship(
        "Programme",
    )
