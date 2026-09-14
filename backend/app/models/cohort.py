from __future__ import annotations

from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Cohort(Base):
    __tablename__ = "cohorts"

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

    # Collective jackpot configuration.
    target_xp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1_500_000,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    starts_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    ends_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
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

    memberships: Mapped[list["CohortMembership"]] = relationship(
        "CohortMembership",
        back_populates="cohort",
        cascade="all, delete-orphan",
    )
