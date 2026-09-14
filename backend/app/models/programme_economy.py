from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class ProgrammeEconomy(Base):
    """
    Configuration governing the overall XP economy.

    Only one economy configuration exists per programme.
    """

    __tablename__ = "programme_economies"

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

    jackpot_target_xp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1_500_000,
    )

    # Maximum percentage of the target that one exceptional
    # group penalty can remove.
    max_group_penalty_percent: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
    )

    # Maximum multiplier staff can apply to configurable baseline
    # earning rates.
    max_staff_multiplier: Mapped[float] = mapped_column(
        nullable=False,
        default=1.3,
    )

    # Optional cap used when XP accumulation is ahead of schedule.
    weekly_growth_cap_multiplier: Mapped[float] = mapped_column(
        nullable=False,
        default=1.1,
    )

    group_penalties_enabled: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    multipliers_enabled: Mapped[bool] = mapped_column(
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
