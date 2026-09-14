from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from ..db.models import (
    Attendance,
    AttendanceSession,
    Player,
)
from .xp_rules import XPRuleError, award_rule_xp


ATTENDANCE_RULE_CODE = "attendance"


def check_in(
    db: Session,
    *,
    player: Player,
    attendance_session: AttendanceSession,
    created_by: int | None = None,
) -> Attendance:
    """
    Record one player attendance and award configured attendance XP.

    The XP economy is resolved entirely from PointRule.
    """

    existing = (
        db.query(Attendance)
        .filter(
            Attendance.session_id == attendance_session.id,
            Attendance.player_id == player.id,
        )
        .first()
    )

    if existing:
        return existing

    if not attendance_session.active:
        raise ValueError("Attendance session is no longer active.")

    if attendance_session.expires_at <= datetime.utcnow():
        raise ValueError("Attendance session has expired.")

    if player.suspended or not player.active:
        raise ValueError("Player is not active.")

    if player.group_id is None:
        raise ValueError("Player is not assigned to a group.")

    if (
        attendance_session.group_id is not None
        and attendance_session.group_id != player.group_id
    ):
        raise ValueError(
            "Player is not eligible for this attendance session."
        )

    attendance = Attendance(
        session_id=attendance_session.id,
        player_id=player.id,
        xp_awarded=0,
    )

    db.add(attendance)
    db.flush()

    try:
        transaction = award_rule_xp(
            db,
            programme_id=attendance_session.programme_id,
            player_id=player.id,
            rule_code=ATTENDANCE_RULE_CODE,
            reference_type="attendance",
            reference_id=attendance.id,
            created_by=created_by,
        )
    except XPRuleError as exc:
        raise ValueError(str(exc)) from exc

    attendance.xp_awarded = transaction.amount

    db.flush()

    return attendance
