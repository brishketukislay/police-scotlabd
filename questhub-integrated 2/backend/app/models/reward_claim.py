from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class RewardClaimStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    ISSUED = "issued"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class RewardClaim(Base):
    """
    Concrete reward entitlement for a player or programme.

    A milestone creates a claim.
    Staff then process/issue the real-world reward.
    """

    __tablename__ = "reward_claims"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    milestone_id: Mapped[int] = mapped_column(
        ForeignKey("reward_milestones.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    reward_id: Mapped[int] = mapped_column(
        ForeignKey("rewards.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    player_id: Mapped[int | None] = mapped_column(
        ForeignKey("players.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    cohort_id: Mapped[int | None] = mapped_column(
        ForeignKey("cohorts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    status: Mapped[RewardClaimStatus] = mapped_column(
        Enum(
            RewardClaimStatus,
            name="reward_claim_status",
            native_enum=False,
        ),
        nullable=False,
        default=RewardClaimStatus.PENDING,
        index=True,
    )

    # Used to make milestone processing idempotent.
    claim_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    issued_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    issued_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    staff_note: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        index=True,
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

    milestone: Mapped["RewardMilestone"] = relationship(
        "RewardMilestone",
        back_populates="claims",
    )

    reward: Mapped["Reward"] = relationship(
        "Reward",
    )

    player: Mapped["Player | None"] = relationship(
        "Player",
    )

    cohort: Mapped["Cohort | None"] = relationship(
        "Cohort",
    )

    issued_by: Mapped["User | None"] = relationship(
        "User",
    )
