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


class SkillDefinition(Base):
    """
    Defines an available skill tree.

    This is the template/configuration, not a player's progress.
    """

    __tablename__ = "skill_definitions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    phase_id: Mapped[int | None] = mapped_column(
        ForeignKey("phases.id", ondelete="SET NULL"),
        nullable=True,
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

    # Example:
    # cooking
    # fitness
    # qualification
    # volunteering
    category: Mapped[str] = mapped_column(
        String(80),
        nullable=False,
    )

    # Milestones are configuration rather than player state.
    #
    # Example:
    # [
    #   {"key": "foundation", "xp": 15000, "reward_id": 1},
    #   {"key": "development", "xp": 40000, "reward_id": 2},
    #   {"key": "completion", "xp": 75000, "reward_id": 3}
    # ]
    milestones: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
    )

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

    phase: Mapped["Phase | None"] = relationship(
        "Phase",
    )
