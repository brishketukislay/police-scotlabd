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


class ProgrammeTheme(Base):
    """
    Visual theme configuration.

    Values are data, not frontend constants, allowing authorised
    admins to change the visual identity without redeploying.
    """

    __tablename__ = "programme_themes"

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

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="Default",
    )

    colors: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    fonts: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    effects: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    logo_asset: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
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
