from __future__ import annotations

import enum

from .xp_transaction import XPTransaction


class XPAccountScope(str, enum.Enum):
    PLAYER = "player"
    GROUP = "group"
    COHORT = "cohort"


class XPSourceType(str, enum.Enum):
    ATTENDANCE = "attendance"
    BEHAVIOUR = "behaviour"
    REFLECTION = "reflection"
    ACTIVITY = "activity"
    CHALLENGE = "challenge"
    CIVIC_ACTION = "civic_action"
    KUDOS = "kudos"
    SKILL_MILESTONE = "skill_milestone"
    BADGE = "badge"
    REWARD = "reward"
    STAFF_AWARD = "staff_award"
    PENALTY = "penalty"
    GROUP_PENALTY = "group_penalty"
    MULTIPLIER = "multiplier"
    SYSTEM = "system"


__all__ = [
    "XPAccountScope",
    "XPSourceType",
    "XPTransaction",
]
