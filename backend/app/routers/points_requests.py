from datetime import datetime
import hashlib

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..db.database import get_db
from ..db.models import AuditLog, Player, PlayerAttendanceToken, PointAwardRequest
from ..services.xp import award_xp

router = APIRouter(prefix="/api/points-requests", tags=["point award requests"])


def _hash(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _serialize(r: PointAwardRequest) -> dict:
    return {
        "id": r.id,
        "player_id": r.player_id,
        "gamertag": r.player.gamertag if r.player else None,
        "avatar": r.player.avatar if r.player else None,
        "requested_xp": r.requested_xp,
        "reason": r.reason,
        "status": r.status,
        "reviewed_by": r.reviewed_by,
        "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,
        "review_note": r.review_note,
        "created_at": r.created_at.isoformat() if r.created_at else None,
    }


class PointAwardRequestCreate(BaseModel):
    token: str = Field(..., min_length=10, max_length=300)
    requested_xp: int = Field(..., ge=1, le=5000)
    reason: str = Field(..., min_length=3, max_length=500)


class PointAwardDecision(BaseModel):
    approved_xp: int | None = Field(None, ge=1, le=5000)
    review_note: str | None = Field(None, max_length=500)


@router.post("", status_code=201)
def create_request(payload: PointAwardRequestCreate, db: Session = Depends(get_db)):
    token = db.query(PlayerAttendanceToken).filter(
        PlayerAttendanceToken.token_hash == _hash(payload.token.strip()),
        PlayerAttendanceToken.active.is_(True),
    ).first()
    if not token:
        raise HTTPException(status_code=404, detail="Quest QR is invalid or has been rotated.")

    player = db.query(Player).filter(Player.id == token.player_id, Player.active.is_(True)).first()
    if not player or player.suspended:
        raise HTTPException(status_code=400, detail="Player is not eligible for a point request.")

    pending = db.query(PointAwardRequest).filter(
        PointAwardRequest.player_id == player.id,
        PointAwardRequest.status == "pending",
    ).count()
    if pending >= 5:
        raise HTTPException(status_code=429, detail="This player already has several requests awaiting review.")

    request = PointAwardRequest(
        player_id=player.id,
        requested_xp=payload.requested_xp,
        reason=payload.reason.strip(),
        status="pending",
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return {"success": True, "request": _serialize(request)}


@router.get("")
def list_requests(
    status: str = Query("pending", pattern="^(pending|approved|rejected|all)$"),
    user=Depends(require_roles("admin", "youth_worker")),
    db: Session = Depends(get_db),
):
    q = db.query(PointAwardRequest).join(Player)
    if status != "all":
        q = q.filter(PointAwardRequest.status == status)
    rows = q.order_by(PointAwardRequest.created_at.desc()).limit(200).all()
    return [_serialize(r) for r in rows]


@router.post("/{request_id}/approve")
def approve_request(
    request_id: int,
    payload: PointAwardDecision = PointAwardDecision(),
    user=Depends(require_roles("admin", "youth_worker")),
    db: Session = Depends(get_db),
):
    r = db.query(PointAwardRequest).filter(PointAwardRequest.id == request_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Point request not found.")
    if r.status != "pending":
        raise HTTPException(status_code=409, detail="This request has already been reviewed.")
    player = db.query(Player).filter(Player.id == r.player_id, Player.active.is_(True)).first()
    if not player or player.suspended:
        raise HTTPException(status_code=400, detail="Player is no longer eligible for this request.")

    amount = payload.approved_xp or r.requested_xp
    try:
        transaction = award_xp(
            db,
            programme_id=player.programme_id,
            player_id=player.id,
            amount=amount,
            group_amount=0,
            transaction_type="point_request",
            reason=f"Approved point request #{r.id}: {r.reason}",
            reference_type="point_award_request",
            reference_id=r.id,
            created_by=user.id,
        )
        r.status = "approved"
        r.reviewed_by = user.id
        r.reviewed_at = datetime.utcnow()
        r.review_note = payload.review_note
        db.add(AuditLog(
            user_id=user.id,
            action="xp.point_request.approved",
            entity_type="point_award_request",
            entity_id=r.id,
            details=f"player_id={player.id};requested={r.requested_xp};approved={amount};reason={r.reason}",
        ))
        db.commit()
        db.refresh(r)
        return {"success": True, "request": _serialize(r), "transaction_id": transaction.id, "approved_xp": amount}
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{request_id}/reject")
def reject_request(
    request_id: int,
    payload: PointAwardDecision = PointAwardDecision(),
    user=Depends(require_roles("admin", "youth_worker")),
    db: Session = Depends(get_db),
):
    r = db.query(PointAwardRequest).filter(PointAwardRequest.id == request_id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Point request not found.")
    if r.status != "pending":
        raise HTTPException(status_code=409, detail="This request has already been reviewed.")
    r.status = "rejected"
    r.reviewed_by = user.id
    r.reviewed_at = datetime.utcnow()
    r.review_note = payload.review_note or "Request declined by youth worker."
    db.add(AuditLog(
        user_id=user.id,
        action="xp.point_request.rejected",
        entity_type="point_award_request",
        entity_id=r.id,
        details=f"player_id={r.player_id};requested={r.requested_xp};reason={r.reason};note={r.review_note}",
    ))
    db.commit()
    db.refresh(r)
    return {"success": True, "request": _serialize(r)}
