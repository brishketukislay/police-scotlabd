from datetime import datetime, timedelta
import hashlib
import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import require_roles, get_current_user
from ..db.database import get_db
from ..db.models import (
    Attendance,
    AttendanceSession,
    Player,
    PlayerAttendanceToken,
    Programme,
    YouthGroup,
)
from ..schemas.attendance import (
    AttendanceCheckInRequest,
    AttendanceResponse,
)
from ..services.attendance import check_in


router = APIRouter(
    prefix="/api/attendance",
    tags=["attendance"],
)


# ============================================================
# HELPERS
# ============================================================

def get_active_programme(db: Session) -> Programme:
    programme = (
        db.query(Programme)
        .filter(Programme.active == True)
        .first()
    )

    if programme is None:
        raise HTTPException(
            status_code=404,
            detail="No active programme configured.",
        )

    return programme


# ============================================================
# PERSONAL PLAYER QR
# ============================================================

def _qr_hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()

@router.post("/player-qr/rotate")
def rotate_player_qr(user=Depends(require_roles("player")), db:Session=Depends(get_db)):
    player=db.query(Player).filter(Player.user_id==user.id,Player.active.is_(True)).first()
    if not player: raise HTTPException(status_code=404,detail="Player profile not found.")
    raw=secrets.token_urlsafe(32)
    token=db.query(PlayerAttendanceToken).filter(PlayerAttendanceToken.player_id==player.id).first()
    if not token:
        token=PlayerAttendanceToken(player_id=player.id,token_hash=_qr_hash(raw),active=True); db.add(token)
    else:
        token.token_hash=_qr_hash(raw); token.active=True; token.rotated_at=datetime.utcnow()
    db.commit(); return {"success":True,"token":raw,"format":"questhub-attendance-v1"}

@router.get("/player-qr")
def player_qr(user=Depends(require_roles("player")), db:Session=Depends(get_db)):
    player=db.query(Player).filter(Player.user_id==user.id,Player.active.is_(True)).first()
    if not player: raise HTTPException(status_code=404,detail="Player profile not found.")
    raw=secrets.token_urlsafe(32)
    token=db.query(PlayerAttendanceToken).filter(PlayerAttendanceToken.player_id==player.id).first()
    if not token:
        token=PlayerAttendanceToken(player_id=player.id,token_hash=_qr_hash(raw),active=True); db.add(token)
    else:
        token.token_hash=_qr_hash(raw); token.active=True; token.rotated_at=datetime.utcnow()
    db.commit()
    return {"success":True,"token":raw,"format":"questhub-attendance-v1"}

class StaffScanQRRequest(BaseModel):
    token: str = Field(...,min_length=10,max_length=200)
    session_id: int | None = None

@router.post("/scan-player-qr")
def scan_player_qr(payload:StaffScanQRRequest,user=Depends(require_roles("admin","youth_worker")),db:Session=Depends(get_db)):
    token=db.query(PlayerAttendanceToken).filter(PlayerAttendanceToken.token_hash==_qr_hash(payload.token.strip()),PlayerAttendanceToken.active.is_(True)).first()
    if not token: raise HTTPException(status_code=404,detail="Attendance QR is invalid or rotated.")
    player=db.query(Player).filter(Player.id==token.player_id,Player.active.is_(True)).first()
    if not player or player.suspended: raise HTTPException(status_code=400,detail="Player is not eligible for attendance.")
    session=db.get(AttendanceSession,payload.session_id) if payload.session_id else None
    if session is None:
        session=db.query(AttendanceSession).filter(AttendanceSession.programme_id==player.programme_id,AttendanceSession.active.is_(True)).order_by(AttendanceSession.id.desc()).first()
    if not session: raise HTTPException(status_code=404,detail="No active attendance session.")
    if session.programme_id!=player.programme_id: raise HTTPException(status_code=400,detail="Player and session are in different programmes.")
    if session.group_id is not None and session.group_id!=player.group_id: raise HTTPException(status_code=400,detail="Player is not eligible for this group session.")
    try:
        attendance=check_in(db,player=player,attendance_session=session,created_by=user.id); db.commit(); db.refresh(attendance)
        return {"success":True,"attendance_id":attendance.id,"player":{"id":player.id,"gamertag":player.gamertag,"avatar":player.avatar},"session_id":session.id,"xp_awarded":attendance.xp_awarded,"checked_in_at":attendance.checked_in_at}
    except ValueError as exc:
        db.rollback(); raise HTTPException(status_code=400,detail=str(exc)) from exc


# ============================================================
# STAFF ATTENDANCE SESSION
# ============================================================

class AttendanceStartRequest(BaseModel):
    group_id: int | None = None

    expires_in_minutes: int = Field(
        default=15,
        ge=1,
        le=120,
    )


@router.post("/start")
def start_attendance(
    payload: AttendanceStartRequest,
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Start a short-lived attendance session for staff.

    The returned code is safe to display as a QR/text code.
    It does not expose player identity.
    """

    programme = get_active_programme(db)

    group = None

    if payload.group_id is not None:
        group = (
            db.query(YouthGroup)
            .filter(
                YouthGroup.id == payload.group_id,
                YouthGroup.programme_id == programme.id,
                YouthGroup.active == True,
            )
            .first()
        )

        if group is None:
            raise HTTPException(
                status_code=404,
                detail="Group not found.",
            )

    # Expire previous active sessions created by this staff member.
    db.query(AttendanceSession).filter(
        AttendanceSession.created_by == user.id,
        AttendanceSession.active == True,
    ).update(
        {
            AttendanceSession.active: False,
        },
        synchronize_session=False,
    )

    code = secrets.token_urlsafe(9)[:12]

    session = AttendanceSession(
        programme_id=programme.id,
        group_id=group.id if group else None,
        code=code,
        expires_at=(
            datetime.utcnow()
            + timedelta(
                minutes=payload.expires_in_minutes
            )
        ),
        active=True,
        created_by=user.id,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return {
        "success": True,
        "id": session.id,
        "code": session.code,
        "group_id": session.group_id,
        "expires_at": session.expires_at.isoformat(),
        "expires_in_seconds": (
            payload.expires_in_minutes * 60
        ),
    }


# ============================================================
# PLAYER CHECK-IN
# ============================================================

class AttendanceCodeCheckInRequest(BaseModel):
    code: str = Field(
        ...,
        min_length=3,
        max_length=32,
    )


@router.post(
    "/check-in",
    response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED,
)
def check_in_player(
    payload: AttendanceCodeCheckInRequest,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    Register the authenticated player against an active
    attendance session using the short-lived session code.
    """

    player = (
        db.query(Player)
        .filter(
            Player.user_id == user.id,
            Player.active == True,
        )
        .first()
    )

    if not player:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Player profile not found.",
        )

    attendance_session = (
        db.query(AttendanceSession)
        .filter(
            AttendanceSession.code == payload.code.strip(),
        )
        .first()
    )

    if not attendance_session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Attendance code not found.",
        )

    try:
        attendance = check_in(
            db,
            player=player,
            attendance_session=attendance_session,
            created_by=user.id,
        )

        db.commit()
        db.refresh(attendance)

        return attendance

    except ValueError as exc:
        db.rollback()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
