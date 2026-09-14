from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..db.models import PointRule, XPTransaction
from .xp import award_xp


class XPRuleError(ValueError):
    """Raised when an XP economy rule cannot be used."""


@dataclass(frozen=True)
class ResolvedXPRule:
    """Immutable economy configuration resolved for one operation."""

    id: int
    programme_id: int
    code: str
    name: str
    individual_xp: int
    group_xp: int
    weekly_cap: int | None
    awards_per_week: float
    individual_award_cap: int | None
    group_award_cap: int | None

    def individual_amount(self) -> int:
        amount = self.individual_xp

        if self.individual_award_cap is not None:
            amount = min(amount, self.individual_award_cap)

        return amount

    def group_amount(self) -> int:
        amount = self.group_xp

        if self.group_award_cap is not None:
            amount = min(amount, self.group_award_cap)

        return amount


def get_rule(
    db: Session,
    *,
    programme_id: int,
    code: str,
) -> ResolvedXPRule:
    """Resolve an enabled PointRule for a programme."""

    normalized_code = code.strip().lower()

    if not normalized_code:
        raise XPRuleError("XP rule code cannot be empty.")

    rule = (
        db.query(PointRule)
        .filter(
            PointRule.programme_id == programme_id,
            PointRule.code == normalized_code,
        )
        .first()
    )

    if rule is None:
        raise XPRuleError(
            f"No XP rule is configured for '{normalized_code}'."
        )

    if not rule.enabled:
        raise XPRuleError(
            f"The XP rule '{normalized_code}' is disabled."
        )

    if rule.individual_xp <= 0 and rule.group_xp <= 0:
        raise XPRuleError(
            f"The XP rule '{normalized_code}' has no positive reward."
        )

    return ResolvedXPRule(
        id=rule.id,
        programme_id=rule.programme_id,
        code=rule.code,
        name=rule.name,
        individual_xp=rule.individual_xp,
        group_xp=rule.group_xp,
        weekly_cap=rule.weekly_cap,
        awards_per_week=float(rule.awards_per_week or 0),
        individual_award_cap=rule.individual_award_cap,
        group_award_cap=rule.group_award_cap,
    )


def _week_start(now: datetime) -> datetime:
    """Return Monday 00:00 for the UTC week containing ``now``."""

    current = now.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    return current - timedelta(days=current.weekday())


def weekly_rule_usage(
    db: Session,
    *,
    rule: ResolvedXPRule,
    player_id: int,
    now: datetime | None = None,
) -> tuple[int, int]:
    """
    Return:

        (positive individual XP awarded this week, award count)

    Usage is calculated from the immutable XP ledger.
    """

    current_time = now or datetime.utcnow()
    start = _week_start(current_time)

    row = (
        db.query(
            func.coalesce(func.sum(XPTransaction.amount), 0),
            func.count(XPTransaction.id),
        )
        .filter(
            XPTransaction.programme_id == rule.programme_id,
            XPTransaction.player_id == player_id,
            XPTransaction.transaction_type == rule.code,
            XPTransaction.created_at >= start,
            XPTransaction.created_at < current_time,
            XPTransaction.amount > 0,
        )
        .one()
    )

    return int(row[0] or 0), int(row[1] or 0)


def apply_rule_limits(
    db: Session,
    *,
    rule: ResolvedXPRule,
    player_id: int,
    individual_amount: int,
    group_amount: int,
    now: datetime | None = None,
) -> tuple[int, int]:
    """
    Apply all configured limits to one future award.

    Weekly XP cap applies to the player's individual XP ledger amount.
    Group XP is deliberately not counted against the player's personal cap.

    The operation either produces a positive individual award or a positive
    group award. A completely zero result is rejected.
    """

    if not isinstance(individual_amount, int):
        raise XPRuleError("Individual XP must be an integer.")

    if not isinstance(group_amount, int):
        raise XPRuleError("Group XP must be an integer.")

    if individual_amount < 0:
        raise XPRuleError("Individual XP cannot be negative.")

    if group_amount < 0:
        raise XPRuleError("Group XP cannot be negative.")

    if rule.individual_award_cap is not None:
        individual_amount = min(
            individual_amount,
            rule.individual_award_cap,
        )

    if rule.group_award_cap is not None:
        group_amount = min(
            group_amount,
            rule.group_award_cap,
        )

    used_xp, award_count = weekly_rule_usage(
        db,
        rule=rule,
        player_id=player_id,
        now=now,
    )

    if (
        rule.awards_per_week > 0
        and award_count >= rule.awards_per_week
    ):
        raise XPRuleError(
            f"XP rule '{rule.code}' has reached its weekly award limit."
        )

    if rule.weekly_cap is not None:
        remaining = rule.weekly_cap - used_xp

        if remaining <= 0:
            raise XPRuleError(
                f"XP rule '{rule.code}' has reached its weekly XP cap."
            )

        individual_amount = min(
            individual_amount,
            remaining,
        )

    if individual_amount == 0 and group_amount == 0:
        raise XPRuleError(
            f"XP rule '{rule.code}' produced no award after limits."
        )

    return individual_amount, group_amount


def award_rule_xp(
    db: Session,
    *,
    programme_id: int,
    player_id: int,
    rule_code: str,
    transaction_type: str | None = None,
    reason: str | None = None,
    reference_type: str | None = None,
    reference_id: int | None = None,
    idempotency_key: str | None = None,
    created_by: int | None = None,
) -> XPTransaction:
    """
    Award XP entirely from a configured PointRule.

    This is the preferred operation for feature code.

    Feature services identify *what happened* using ``rule_code``.
    They do not provide XP amounts.
    """

    rule = get_rule(
        db,
        programme_id=programme_id,
        code=rule_code,
    )

    individual_amount, group_amount = apply_rule_limits(
        db,
        rule=rule,
        player_id=player_id,
        individual_amount=rule.individual_amount(),
        group_amount=rule.group_amount(),
    )

    return award_xp(
        db,
        programme_id=programme_id,
        player_id=player_id,
        amount=individual_amount,
        group_amount=group_amount,
        transaction_type=transaction_type or rule.code,
        reason=reason or rule.name,
        reference_type=reference_type,
        reference_id=reference_id,
        idempotency_key=idempotency_key,
        created_by=created_by,
    )
