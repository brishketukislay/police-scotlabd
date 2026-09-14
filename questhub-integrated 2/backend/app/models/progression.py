from __future__ import annotations

import enum
import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


if TYPE_CHECKING:
    from app.models.player import Player
    from app.models.programme import Programme
    from app.models.user import User


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SkillTreeStatus(str, enum.Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"
    ARCHIVED = "archived"


class MilestoneStatus(str, enum.Enum):
    LOCKED = "locked"
    AVAILABLE = "available"
    COMPLETED = "completed"
    SKIPPED = "skipped"


class BadgeTier(str, enum.Enum):
    IRON = "iron"
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PRESTIGE = "prestige"


class CosmeticType(str, enum.Enum):
    PROFILE_FRAME = "profile_frame"
    AVATAR = "avatar"
    AVATAR_ITEM = "avatar_item"
    BACKGROUND = "background"
    SOUND = "sound"
    EFFECT = "effect"
    BADGE = "badge"


class SkillDefinition(Base):
    """
    Configurable catalogue entry describing a skill a player can work on.

    Examples:

        Cooking
        Fitness
        SVQ completion
        Job preparation
        Confidence
        Creative skill

    The platform does not dictate what a 'skill' is. Youth workers and
    programme administrators configure this around the participant.
    """

    __tablename__ = "skill_definitions"

    __table_args__ = (
        UniqueConstraint(
            "programme_id",
            "slug",
            name="uq_skill_definition_programme_slug",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    programme_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "programmes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    icon_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    colour: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    programme: Mapped["Programme"] = relationship(
        "Programme",
    )

    player_trees: Mapped[list["PlayerSkillTree"]] = relationship(
        "PlayerSkillTree",
        back_populates="skill_definition",
    )


class SkillTreeTemplate(Base):
    """
    Reusable progression template.

    This lets admins define different progression structures without
    changing application code.

    A template might contain:

        Tier 1 -> 15,000 XP -> £5
        Tier 2 -> 40,000 XP -> £10
        Tier 3 -> 75,000 XP -> £20

    But another programme could use entirely different thresholds.
    """

    __tablename__ = "skill_tree_templates"

    __table_args__ = (
        UniqueConstraint(
            "programme_id",
            "slug",
            name="uq_skill_tree_template_programme_slug",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    programme_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "programmes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    programme: Mapped["Programme"] = relationship(
        "Programme",
    )

    milestones: Mapped[list["SkillTreeMilestone"]] = relationship(
        "SkillTreeMilestone",
        back_populates="template",
        cascade="all, delete-orphan",
        order_by="SkillTreeMilestone.sort_order",
    )


class SkillTreeMilestone(Base):
    """
    One milestone in a skill-tree template.

    XP thresholds are configurable.

    Importantly, the threshold is not necessarily the player's global XP
    balance. It represents the requirement configured for this milestone.
    """

    __tablename__ = "skill_tree_milestones"

    __table_args__ = (
        UniqueConstraint(
            "template_id",
            "sort_order",
            name="uq_skill_tree_milestone_template_order",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    template_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "skill_tree_templates.id",
            ondelete="CASCADE",
        ),
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

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    """
    XP required to complete this milestone.

    Example:

        15000
        40000
        75000
    """

    required_xp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    """
    XP awarded when the milestone is completed.

    Keeping this separate from required_xp lets the programme choose
    whether milestone completion itself gives additional XP.
    """

    xp_reward: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    reward_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "rewards.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    badge_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "badges.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    cosmetic_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "cosmetics.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    template: Mapped["SkillTreeTemplate"] = relationship(
        "SkillTreeTemplate",
        back_populates="milestones",
    )


class PlayerSkillTree(Base):
    """
    A player's active instance of a skill tree.

    The template describes what the programme has configured.

    This model records the individual participant's actual journey.
    """

    __tablename__ = "player_skill_trees"

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    player_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "players.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    skill_definition_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "skill_definitions.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    template_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "skill_tree_templates.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    status: Mapped[SkillTreeStatus] = mapped_column(
        Enum(
            SkillTreeStatus,
            name="skill_tree_status",
            native_enum=False,
        ),
        nullable=False,
        default=SkillTreeStatus.ACTIVE,
        index=True,
    )

    """
    Current progress within this particular tree.

    This is deliberately separate from Player.current_xp.
    """

    progress_xp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    current_milestone_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    reset_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    completion_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    youth_worker_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    player: Mapped["Player"] = relationship(
        "Player",
    )

    skill_definition: Mapped["SkillDefinition"] = relationship(
        "SkillDefinition",
        back_populates="player_trees",
    )

    template: Mapped["SkillTreeTemplate"] = relationship(
        "SkillTreeTemplate",
    )

    milestones: Mapped[list["PlayerSkillTreeMilestone"]] = relationship(
        "PlayerSkillTreeMilestone",
        back_populates="player_skill_tree",
        cascade="all, delete-orphan",
        order_by="PlayerSkillTreeMilestone.sort_order",
    )

    def add_progress(self, amount: int) -> None:
        if amount <= 0:
            raise ValueError(
                "Skill tree progress must be greater than zero."
            )

        if self.status != SkillTreeStatus.ACTIVE:
            raise ValueError(
                "Cannot add progress to an inactive skill tree."
            )

        self.progress_xp += amount

    def complete(self) -> None:
        if self.status != SkillTreeStatus.ACTIVE:
            raise ValueError(
                "Only an active skill tree can be completed."
            )

        self.status = SkillTreeStatus.COMPLETED
        self.completed_at = utc_now()
        self.completion_number += 1

    def reset(self) -> None:
        """
        Reset the active goal after completion.

        Historical completion records should remain intact in the
        milestone/completion audit domain.

        This method only resets the active progression state.
        """

        self.status = SkillTreeStatus.ACTIVE
        self.progress_xp = 0
        self.current_milestone_order = 1
        self.started_at = utc_now()
        self.completed_at = None
        self.reset_at = utc_now()


class PlayerSkillTreeMilestone(Base):
    """
    Snapshot of a milestone assigned to a particular player.

    We snapshot the relevant configuration instead of relying exclusively
    on the template.

    This prevents an administrator changing a template halfway through
    someone's journey from silently rewriting their historical progress.
    """

    __tablename__ = "player_skill_tree_milestones"

    __table_args__ = (
        UniqueConstraint(
            "player_skill_tree_id",
            "sort_order",
            name="uq_player_skill_tree_milestone_order",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    player_skill_tree_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "player_skill_trees.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    template_milestone_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey(
            "skill_tree_milestones.id",
            ondelete="SET NULL",
        ),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    required_xp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    xp_reward: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    status: Mapped[MilestoneStatus] = mapped_column(
        Enum(
            MilestoneStatus,
            name="milestone_status",
            native_enum=False,
        ),
        nullable=False,
        default=MilestoneStatus.LOCKED,
        index=True,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    """
    JSON snapshot of reward configuration.

    This is intentionally immutable after assignment.

    Example:

        {
            "reward_type": "gift_card",
            "value_pence": 1000,
            "reward_name": "Love2shop £10"
        }
    """

    reward_snapshot: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    player_skill_tree: Mapped["PlayerSkillTree"] = relationship(
        "PlayerSkillTree",
        back_populates="milestones",
    )

    def mark_available(self) -> None:
        if self.status == MilestoneStatus.LOCKED:
            self.status = MilestoneStatus.AVAILABLE

    def complete(self) -> None:
        if self.status not in (
            MilestoneStatus.AVAILABLE,
            MilestoneStatus.LOCKED,
        ):
            raise ValueError(
                "Milestone cannot be completed in its current state."
            )

        self.status = MilestoneStatus.COMPLETED
        self.completed_at = utc_now()


class Badge(Base):
    """
    Configurable badge definition.

    Badge progression should be data-driven.

    Example:

        Iron
        Bronze
        Silver
        Gold Prestige
    """

    __tablename__ = "badges"

    __table_args__ = (
        UniqueConstraint(
            "programme_id",
            "slug",
            name="uq_badge_programme_slug",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    programme_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "programmes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    tier: Mapped[BadgeTier] = mapped_column(
        Enum(
            BadgeTier,
            name="badge_tier",
            native_enum=False,
        ),
        nullable=False,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    xp_reward: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    group_xp_reward: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    profile_frame: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    icon_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    programme: Mapped["Programme"] = relationship(
        "Programme",
    )

    awards: Mapped[list["PlayerBadge"]] = relationship(
        "PlayerBadge",
        back_populates="badge",
        cascade="all, delete-orphan",
    )


class PlayerBadge(Base):
    """
    Immutable-ish record that a player earned a badge.

    We retain every award, even if the player's active skill tree is later
    reset.
    """

    __tablename__ = "player_badges"

    __table_args__ = (
        UniqueConstraint(
            "player_id",
            "badge_id",
            "achievement_number",
            name="uq_player_badge_achievement",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    player_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "players.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    badge_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "badges.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    achievement_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    awarded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    player: Mapped["Player"] = relationship(
        "Player",
    )

    badge: Mapped["Badge"] = relationship(
        "Badge",
        back_populates="awards",
    )


class Cosmetic(Base):
    """
    Configurable digital cosmetic.

    Cosmetics have no monetary value and cannot be redeemed as cash.
    """

    __tablename__ = "cosmetics"

    __table_args__ = (
        UniqueConstraint(
            "programme_id",
            "slug",
            name="uq_cosmetic_programme_slug",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    programme_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "programmes.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(100),
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
    )

    asset_key: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    configuration: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    programme: Mapped["Programme"] = relationship(
        "Programme",
    )


class PlayerCosmetic(Base):
    """
    Cosmetic unlocked by a player.

    Unlocking a cosmetic and currently equipping it are separate concepts.
    """

    __tablename__ = "player_cosmetics"

    __table_args__ = (
        UniqueConstraint(
            "player_id",
            "cosmetic_id",
            name="uq_player_cosmetic",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )

    player_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "players.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    cosmetic_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey(
            "cosmetics.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    unlocked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    equipped: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
    )

    player: Mapped["Player"] = relationship(
        "Player",
    )

    cosmetic: Mapped["Cosmetic"] = relationship(
        "Cosmetic",
    )
