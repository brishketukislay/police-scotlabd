from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .core import Base


class RewardGameType(str, enum.Enum):
    SCRATCH = "scratch"
    WHEEL = "wheel"


class RewardGamePlayStatus(str, enum.Enum):
    AVAILABLE = "available"
    PLAYED = "played"
    CANCELLED = "cancelled"


class RewardGame(Base):
    __tablename__ = "reward_games"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id", ondelete="CASCADE"),
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

    game_type: Mapped[RewardGameType] = mapped_column(
        Enum(
            RewardGameType,
            name="reward_game_type",
            native_enum=False,
        ),
        nullable=False,
        index=True,
    )

    prize_values: Mapped[list[int]] = mapped_column(
        JSON,
        nullable=False,
    )

    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )

    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        index=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    show_upcoming: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    plays: Mapped[list["PlayerRewardGame"]] = relationship(
        "PlayerRewardGame",
        back_populates="game",
        cascade="all, delete-orphan",
    )


class PlayerRewardGame(Base):
    __tablename__ = "player_reward_games"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    game_id: Mapped[int] = mapped_column(
        ForeignKey("reward_games.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[RewardGamePlayStatus] = mapped_column(
        Enum(
            RewardGamePlayStatus,
            name="reward_game_play_status",
            native_enum=False,
        ),
        nullable=False,
        default=RewardGamePlayStatus.AVAILABLE,
        index=True,
    )

    awarded_xp: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    xp_transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("xp_transactions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    played_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    granted_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    granted_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    play_metadata: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    game: Mapped["RewardGame"] = relationship(
        "RewardGame",
        back_populates="plays",
    )

    player: Mapped["Player"] = relationship(
        "Player",
    )

    __table_args__ = ()
