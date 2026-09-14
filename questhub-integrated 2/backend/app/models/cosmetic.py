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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class CosmeticType(str, enum.Enum):
    AVATAR = "avatar"
    FRAME = "frame"
    BACKGROUND = "background"
    SOUND = "sound"
    EFFECT = "effect"
    TITLE = "title"


class Cosmetic(Base):
    """
    Catalogue of visual/audio items that players can unlock.

    Cosmetics contain no player-specific state.
    """

    __tablename__ = "cosmetics"

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

    cosmetic_type: Mapped[CosmeticType] = mapped_column(
        Enum(
            CosmeticType,
            name="cosmetic_type",
            native_enum=False,
        ),
        nullable=False,
        index=True,
    )

    asset_key: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    rarity: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Optional information used by the frontend renderer.
    visual_config: Mapped[dict] = mapped_column(
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

    position: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
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

    player_cosmetics: Mapped[list["PlayerCosmetic"]] = relationship(
        "PlayerCosmetic",
        back_populates="cosmetic",
    )
