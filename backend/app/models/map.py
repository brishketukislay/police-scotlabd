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


class GameMap(Base):
    """
    Configurable visual map.

    The actual frontend renders this data. No geographic implementation
    is assumed here, so the map can be replaced later.
    """

    __tablename__ = "game_maps"

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
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # SVG/image/illustration URL or frontend asset identifier.
    background_asset: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    # Allows different map rendering strategies later.
    renderer: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="illustrated",
    )

    # Arbitrary visual configuration.
    config: Mapped[dict] = mapped_column(
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

    locations: Mapped[list["MapLocation"]] = relationship(
        "MapLocation",
        back_populates="game_map",
        cascade="all, delete-orphan",
    )
