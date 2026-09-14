from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class CohortMembership(Base):
    __tablename__ = "cohort_memberships"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    cohort_id: Mapped[int] = mapped_column(
        ForeignKey("cohorts.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    left_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    cohort: Mapped["Cohort"] = relationship(
        "Cohort",
        back_populates="memberships",
    )

    group: Mapped["Group"] = relationship(
        "Group",
    )

    __table_args__ = (
        UniqueConstraint(
            "cohort_id",
            "group_id",
            name="uq_cohort_group",
        ),
    )
