"""Compatibility layer for the historical gamification model module.

The application's authoritative ORM models live in app.db.models.core.

This module MUST NOT define duplicate SQLAlchemy classes for tables already
owned by core.py.

GroupXPTransaction is retained here because it is a distinct table.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base
from .core import (
    Badge,
    PlayerBadge,
    Reward,
    RewardClaim,
    SkillMilestone,
    SkillTree,
)


# -------------------------------------------------------------------------
# ENUMS
# -------------------------------------------------------------------------

class XPSourceType(str, Enum):
    ATTENDANCE = "attendance"
    BEHAVIOUR_BASELINE = "behaviour_baseline"
    PROCESSING_CHAT = "processing_chat"
    GAME_PARTICIPATION = "game_participation"
    CHALLENGE = "challenge"
    CHALLENGE_BONUS = "challenge_bonus"
    CIVIC_ACTION = "civic_action"
    SKILL_TREE = "skill_tree"
    BADGE = "badge"
    LOOT_WHEEL = "loot_wheel"
    COMMUNITY_AWARD = "community_award"
    RESTORATIVE_ACTION = "restorative_action"
    MANUAL = "manual"
    PENALTY = "penalty"
    GROUP_PENALTY = "group_penalty"
    MULTIPLIER = "multiplier"
    SYSTEM = "system"


class XPTransactionStatus(str, Enum):
    POSTED = "posted"
    VOIDED = "voided"


class RewardType(str, Enum):
    VOUCHER = "voucher"
    PHYSICAL = "physical"
    DIGITAL = "digital"
    GROUP = "group"
    FOOD = "food"
    COSMETIC = "cosmetic"


class RewardClaimStatus(str, Enum):
    ELIGIBLE = "eligible"
    PENDING = "pending"
    APPROVED = "approved"
    FULFILLED = "fulfilled"
    DECLINED = "declined"
    CANCELLED = "cancelled"


class SkillTreeStatus(str, Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class BadgeTier(str, Enum):
    IRON = "iron"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD_PRESTIGE = "gold_prestige"


# -------------------------------------------------------------------------
# DISTINCT COLLECTIVE XP LEDGER
# -------------------------------------------------------------------------

class GroupXPTransaction(Base):
    """Collective/group XP ledger.

    This is intentionally separate from core.XPTransaction.
    """

    __tablename__ = "group_xp_transactions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id"),
        nullable=True,
        index=True,
    )

    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    source_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=XPTransactionStatus.POSTED.value,
        index=True,
    )

    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    reversal_of_id: Mapped[int | None] = mapped_column(
        ForeignKey("group_xp_transactions.id"),
        nullable=True,
        index=True,
    )

    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        server_default=func.now(),
        index=True,
    )

    reversal_of: Mapped["GroupXPTransaction | None"] = relationship(
        remote_side=[id],
        foreign_keys=[reversal_of_id],
    )

    __table_args__ = (
        Index(
            "ix_group_xp_transactions_programme_created",
            "programme_id",
            "created_at",
        ),
    )


# -------------------------------------------------------------------------
# EXPLICIT COMPATIBILITY EXPORTS
# -------------------------------------------------------------------------

__all__ = [
    "XPSourceType",
    "XPTransactionStatus",
    "RewardType",
    "RewardClaimStatus",
    "SkillTreeStatus",
    "BadgeTier",
    "GroupXPTransaction",
    "SkillTree",
    "SkillMilestone",
    "Badge",
    "PlayerBadge",
    "Reward",
    "RewardClaim",
]
