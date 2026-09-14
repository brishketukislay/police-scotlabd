from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class PlatformConfig(Base):
    """
    Programme-level visual and behavioural configuration.

    Keep this separate from operational data such as XP transactions.
    Admins can change presentation/configuration without mutating history.
    """

    __tablename__ = "platform_configs"

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

    app_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        default="Digital Youth Platform",
    )

    primary_colour: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="#6C5CE7",
    )

    secondary_colour: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="#00CEC9",
    )

    accent_colour: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="#FDCB6E",
    )

    background_colour: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="#111827",
    )

    # Controls optional platform features.
    #
    # Example:
    # {
    #   "kudos": true,
    #   "public_leaderboard": true,
    #   "flash_challenges": true,
    #   "community_awards": true,
    #   "notifications": true
    # }
    feature_flags: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Centralised frontend settings that don't warrant their own model.
    #
    # Example:
    # {
    #   "max_kudos_per_day": 3,
    #   "leaderboard_refresh_seconds": 15
    # }
    settings: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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
