from app.db.base import Base
"""
Compatibility exports for the application's canonical SQLAlchemy models.

The authoritative model registry is app.db.models.

This module exists for compatibility with code that historically imported
models from app.models.
"""

from app.db.models import (
    AuditLog,
    Attendance,
    AttendanceSession,
    Badge,
    Challenge,
    ChallengeAttempt,
    CommunityAward,
    ConductIncident,
    ConductRule,
    EngagementFlag,
    FlashEvent,
    GameDefinition,
    GameMap,
    GroupPenalty,
    Kudos,
    MapLocation,
    Notification,
    Phase,
    PhaseLocation,
    Player,
    PlayerBadge,
    PlayerReward,
    PointRule,
    Programme,
    ProgrammeGame,
    ProgrammeMilestone,
    Resource,
    Reward,
    SkillMilestone,
    SkillTree,
    SystemSetting,
    Theme,
    User,
    XPTransaction,
    YouthGroup,
)

# Compatibility aliases used by newer/older modules.
Group = YouthGroup

# These are enum/value types, not SQLAlchemy model classes.
#
# Import them directly from gamification.py. This is safe because importing
# the module itself would register duplicate ORM models, so we deliberately
# obtain the enum definitions without importing the gamification module here.
#
# The canonical core XPTransaction uses a string transaction_type, so the
# compatibility enum is defined locally.
from enum import Enum


class XPTransactionType(str, Enum):
    ATTENDANCE = "attendance"
    BEHAVIOUR = "behaviour"
    REFLECTION = "reflection"
    ACTIVITY = "activity"
    CHALLENGE = "challenge"
    CIVIC_ACTION = "civic_action"
    COMMUNITY_AWARD = "community_award"
    SKILL_MILESTONE = "skill_milestone"
    BADGE = "badge"
    BONUS = "bonus"
    MULTIPLIER = "multiplier"
    PENALTY = "penalty"
    GROUP_PENALTY = "group_penalty"
    ADMIN_ADJUSTMENT = "admin_adjustment"
    SYSTEM = "system"


__all__ = [
    "AuditLog",
    "Attendance",
    "AttendanceSession",
    "Badge",
    "Challenge",
    "ChallengeAttempt",
    "CommunityAward",
    "ConductIncident",
    "ConductRule",
    "EngagementFlag",
    "FlashEvent",
    "GameDefinition",
    "GameMap",
    "GroupPenalty",
    "Kudos",
    "MapLocation",
    "Notification",
    "Phase",
    "PhaseLocation",
    "Player",
    "PlayerBadge",
    "PlayerReward",
    "PointRule",
    "Programme",
    "ProgrammeGame",
    "ProgrammeMilestone",
    "Resource",
    "Reward",
    "SkillMilestone",
    "SkillTree",
    "SystemSetting",
    "Theme",
    "User",
    "XPTransaction",
    "XPTransactionType",
    "YouthGroup",
    "Group",
]
