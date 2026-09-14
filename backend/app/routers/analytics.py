from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..db.database import get_db
from ..db.models import (
    User,
    Player,
    YouthGroup,
    XPTransaction,
    AttendanceSession,
    Attendance,
    ChallengeAttempt,
    PointAwardRequest,
    AuditLog,
)


router = APIRouter(
    prefix="/api/admin/analytics",
    tags=["analytics"],
)


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


@router.get("")
def analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("admin", "youth_worker")),
):
    """
    Operational programme analytics.

    Read-only. No XP, rewards, attendance or player state is modified.
    """

    now = utc_now()
    week_start = now - timedelta(days=now.weekday())
    day_start = now - timedelta(days=13)

    # ------------------------------------------------------------------
    # PLAYER OVERVIEW
    # ------------------------------------------------------------------

    total_players = (
        db.query(func.count(Player.id))
        .filter(Player.active.is_(True))
        .scalar()
        or 0
    )

    visible_players = (
        db.query(func.count(Player.id))
        .filter(
            Player.active.is_(True),
            Player.public_visible.is_(True),
        )
        .scalar()
        or 0
    )

    # ------------------------------------------------------------------
    # XP
    # ------------------------------------------------------------------

    total_xp = (
        db.query(func.coalesce(func.sum(XPTransaction.amount), 0))
        .scalar()
        or 0
    )

    weekly_xp = (
        db.query(func.coalesce(func.sum(XPTransaction.amount), 0))
        .filter(XPTransaction.created_at >= week_start)
        .scalar()
        or 0
    )

    group_xp = (
        db.query(func.coalesce(func.sum(XPTransaction.group_amount), 0))
        .scalar()
        or 0
    )

    weekly_group_xp = (
        db.query(func.coalesce(func.sum(XPTransaction.group_amount), 0))
        .filter(XPTransaction.created_at >= week_start)
        .scalar()
        or 0
    )

    # XP grouped by transaction source.
    source_rows = (
        db.query(
            XPTransaction.transaction_type,
            func.coalesce(func.sum(XPTransaction.amount), 0),
            func.count(XPTransaction.id),
        )
        .group_by(XPTransaction.transaction_type)
        .order_by(func.sum(XPTransaction.amount).desc())
        .all()
    )

    xp_by_source = [
        {
            "source": row[0],
            "xp": int(row[1] or 0),
            "transactions": int(row[2] or 0),
        }
        for row in source_rows
    ]

    # Recent daily XP.
    daily_rows = (
        db.query(
            func.date(XPTransaction.created_at),
            func.coalesce(func.sum(XPTransaction.amount), 0),
            func.coalesce(func.sum(XPTransaction.group_amount), 0),
        )
        .filter(XPTransaction.created_at >= day_start)
        .group_by(func.date(XPTransaction.created_at))
        .order_by(func.date(XPTransaction.created_at))
        .all()
    )

    daily_xp = [
        {
            "date": str(row[0]),
            "xp": int(row[1] or 0),
            "group_xp": int(row[2] or 0),
        }
        for row in daily_rows
    ]

    # ------------------------------------------------------------------
    # GROUPS
    # ------------------------------------------------------------------

    groups = []

    group_rows = (
        db.query(
            YouthGroup.id,
            YouthGroup.name,
            YouthGroup.active,
            func.count(func.distinct(Player.id)),
            func.coalesce(func.sum(XPTransaction.group_amount), 0),
        )
        .outerjoin(Player, Player.group_id == YouthGroup.id)
        .outerjoin(XPTransaction, XPTransaction.group_id == YouthGroup.id)
        .group_by(
            YouthGroup.id,
            YouthGroup.name,
            YouthGroup.active,
        )
        .order_by(func.sum(XPTransaction.group_amount).desc())
        .all()
    )

    for row in group_rows:
        groups.append(
            {
                "id": row[0],
                "name": row[1],
                "active": bool(row[2]),
                "players": int(row[3] or 0),
                "xp": int(row[4] or 0),
            }
        )

    # ------------------------------------------------------------------
    # ATTENDANCE
    # ------------------------------------------------------------------

    attendance_sessions = (
        db.query(func.count(AttendanceSession.id))
        .scalar()
        or 0
    )

    attendance_checkins = (
        db.query(func.count(Attendance.id))
        .scalar()
        or 0
    )

    attendance_xp = (
        db.query(func.coalesce(func.sum(Attendance.xp_awarded), 0))
        .scalar()
        or 0
    )

    weekly_checkins = (
        db.query(func.count(Attendance.id))
        .filter(Attendance.checked_in_at >= week_start)
        .scalar()
        or 0
    )

    # ------------------------------------------------------------------
    # CHALLENGES
    # ------------------------------------------------------------------

    challenge_attempts = (
        db.query(func.count(ChallengeAttempt.id))
        .scalar()
        or 0
    )

    weekly_challenge_attempts = (
        db.query(func.count(ChallengeAttempt.id))
        .filter(ChallengeAttempt.submitted_at >= week_start)
        .scalar()
        or 0
    )

    # ------------------------------------------------------------------
    # POINT REQUESTS
    # ------------------------------------------------------------------

    pending_requests = (
        db.query(func.count(PointAwardRequest.id))
        .filter(PointAwardRequest.status == "pending")
        .scalar()
        or 0
    )

    approved_requests = (
        db.query(func.count(PointAwardRequest.id))
        .filter(PointAwardRequest.status == "approved")
        .scalar()
        or 0
    )

    rejected_requests = (
        db.query(func.count(PointAwardRequest.id))
        .filter(PointAwardRequest.status == "rejected")
        .scalar()
        or 0
    )

    requested_xp = (
        db.query(func.coalesce(func.sum(PointAwardRequest.requested_xp), 0))
        .filter(PointAwardRequest.status == "approved")
        .scalar()
        or 0
    )

    # ------------------------------------------------------------------
    # AUDIT ACTIVITY
    # ------------------------------------------------------------------

    audit_events_week = (
        db.query(func.count(AuditLog.id))
        .filter(AuditLog.created_at >= week_start)
        .scalar()
        or 0
    )

    # ------------------------------------------------------------------
    # RETURN
    # ------------------------------------------------------------------

    return {
        "generated_at": now.isoformat(),

        "overview": {
            "total_players": int(total_players),
            "public_players": int(visible_players),
            "total_xp": int(total_xp),
            "xp_this_week": int(weekly_xp),
            "group_xp": int(group_xp),
            "group_xp_this_week": int(weekly_group_xp),
        },

        "xp": {
            "by_source": xp_by_source,
            "daily": daily_xp,
        },

        "groups": groups,

        "attendance": {
            "sessions": int(attendance_sessions),
            "checkins": int(attendance_checkins),
            "checkins_this_week": int(weekly_checkins),
            "xp_awarded": int(attendance_xp),
        },

        "challenges": {
            "attempts": int(challenge_attempts),
            "attempts_this_week": int(weekly_challenge_attempts),
        },

        "point_requests": {
            "pending": int(pending_requests),
            "approved": int(approved_requests),
            "rejected": int(rejected_requests),
            "approved_xp": int(requested_xp),
        },

        "operations": {
            "audit_events_this_week": int(audit_events_week),
        },
    }
