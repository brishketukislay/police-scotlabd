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


class XPRuleType(str, enum.Enum):
    ATTENDANCE = "attendance"
    BEHAVIOUR = "behaviour"
    REFLECTION = "reflection"
    ACTIVITY = "activity"
    CHALLENGE = "challenge"
    CIVIC_ACTION = "civic_action"
    COMMUNITY_AWARD = "community_award"
    SKILL_MILESTONE = "skill_milestone"

    BONUS = "bonus"
    MULTIPLIER = "multiplier"

    PENALTY = "penalty"
    GROUP_PENALTY = "group_penalty"

    BADGE = "badge"
    MYSTERY_REWARD = "mystery_reward"


class XPRule(Base):
    """
    Admin-configurable XP rule.

    Rules are programme-specific and can be enabled/disabled without
    changing application code.
    """

    __tablename__ = "xp_rules"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    key: Mapped[str] = mapped_column(
        String(100),
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

    rule_type: Mapped[XPRuleType] = mapped_column(
        Enum(
            XPRuleType,
            name="xp_rule_type",
            native_enum=False,
        ),
        nullable=False,
        index=True,
    )

    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    multiplier: Mapped[float] = mapped_column(
        nullable=False,
        default=1.0,
    )

    # Additional rule-specific configuration.
    config: Mapped[dict] = mapped_column(
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
