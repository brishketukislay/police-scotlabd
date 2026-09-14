from pathlib import Path
import shutil

ROOT = Path.cwd()
if not (ROOT / "app").exists():
    raise SystemExit("Run this script from the QuestHub backend directory.")

def backup(path):
    target = path.with_suffix(path.suffix + ".points-request.bak")
    if not target.exists():
        shutil.copy2(path, target)

# Add the canonical SQLAlchemy model without replacing the rest of core.py.
core = ROOT / "app/db/models/core.py"
text = core.read_text()
if "class PointAwardRequest(Base" not in text:
    backup(core)
    marker = "class AuditLog(Base):"
    model = '''class PointAwardRequest(Base, TimestampMixin):
    """Extra-XP request submitted through a player's personal Quest QR."""

    __tablename__ = "point_award_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requested_xp: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    reviewed_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    review_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    player: Mapped["Player"] = relationship("Player")
    reviewer: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[reviewed_by]
    )


'''
    if marker not in text:
        raise SystemExit("Could not find AuditLog in app/db/models/core.py")
    core.write_text(text.replace(marker, model + marker, 1))

# Export the model.
exports = ROOT / "app/db/models/__init__.py"
text = exports.read_text()
if "PointAwardRequest" not in text:
    backup(exports)
    text = text.replace(
        "    PlayerAttendanceToken,\n",
        "    PlayerAttendanceToken,\n    PointAwardRequest,\n",
        1,
    )
    text = text.replace(
        '    "PlayerAttendanceToken",\n',
        '    "PlayerAttendanceToken",\n    "PointAwardRequest",\n',
        1,
    )
    exports.write_text(text)

# Install the router.
router = ROOT / "app/routers/points_requests.py"
if not router.exists():
    router.write_text('from datetime import datetime\nimport hashlib\n\nfrom fastapi import APIRouter, Depends, HTTPException, Query\nfrom pydantic import BaseModel, Field\nfrom sqlalchemy.orm import Session\n\nfrom ..auth import require_roles\nfrom ..db.database import get_db\nfrom ..db.models import AuditLog, Player, PlayerAttendanceToken, PointAwardRequest\nfrom ..services.xp import award_xp\n\nrouter = APIRouter(prefix="/api/points-requests", tags=["point award requests"])\n\n\ndef _hash(raw: str) -> str:\n    return hashlib.sha256(raw.encode("utf-8")).hexdigest()\n\n\ndef _serialize(r: PointAwardRequest) -> dict:\n    return {\n        "id": r.id,\n        "player_id": r.player_id,\n        "gamertag": r.player.gamertag if r.player else None,\n        "avatar": r.player.avatar if r.player else None,\n        "requested_xp": r.requested_xp,\n        "reason": r.reason,\n        "status": r.status,\n        "reviewed_by": r.reviewed_by,\n        "reviewed_at": r.reviewed_at.isoformat() if r.reviewed_at else None,\n        "review_note": r.review_note,\n        "created_at": r.created_at.isoformat() if r.created_at else None,\n    }\n\n\nclass PointAwardRequestCreate(BaseModel):\n    token: str = Field(..., min_length=10, max_length=300)\n    requested_xp: int = Field(..., ge=1, le=5000)\n    reason: str = Field(..., min_length=3, max_length=500)\n\n\nclass PointAwardDecision(BaseModel):\n    approved_xp: int | None = Field(None, ge=1, le=5000)\n    review_note: str | None = Field(None, max_length=500)\n\n\n@router.post("", status_code=201)\ndef create_request(payload: PointAwardRequestCreate, db: Session = Depends(get_db)):\n    token = db.query(PlayerAttendanceToken).filter(\n        PlayerAttendanceToken.token_hash == _hash(payload.token.strip()),\n        PlayerAttendanceToken.active.is_(True),\n    ).first()\n    if not token:\n        raise HTTPException(status_code=404, detail="Quest QR is invalid or has been rotated.")\n\n    player = db.query(Player).filter(Player.id == token.player_id, Player.active.is_(True)).first()\n    if not player or player.suspended:\n        raise HTTPException(status_code=400, detail="Player is not eligible for a point request.")\n\n    pending = db.query(PointAwardRequest).filter(\n        PointAwardRequest.player_id == player.id,\n        PointAwardRequest.status == "pending",\n    ).count()\n    if pending >= 5:\n        raise HTTPException(status_code=429, detail="This player already has several requests awaiting review.")\n\n    request = PointAwardRequest(\n        player_id=player.id,\n        requested_xp=payload.requested_xp,\n        reason=payload.reason.strip(),\n        status="pending",\n    )\n    db.add(request)\n    db.commit()\n    db.refresh(request)\n    return {"success": True, "request": _serialize(request)}\n\n\n@router.get("")\ndef list_requests(\n    status: str = Query("pending", pattern="^(pending|approved|rejected|all)$"),\n    user=Depends(require_roles("admin", "youth_worker")),\n    db: Session = Depends(get_db),\n):\n    q = db.query(PointAwardRequest).join(Player)\n    if status != "all":\n        q = q.filter(PointAwardRequest.status == status)\n    rows = q.order_by(PointAwardRequest.created_at.desc()).limit(200).all()\n    return [_serialize(r) for r in rows]\n\n\n@router.post("/{request_id}/approve")\ndef approve_request(\n    request_id: int,\n    payload: PointAwardDecision = PointAwardDecision(),\n    user=Depends(require_roles("admin", "youth_worker")),\n    db: Session = Depends(get_db),\n):\n    r = db.query(PointAwardRequest).filter(PointAwardRequest.id == request_id).first()\n    if not r:\n        raise HTTPException(status_code=404, detail="Point request not found.")\n    if r.status != "pending":\n        raise HTTPException(status_code=409, detail="This request has already been reviewed.")\n    player = db.query(Player).filter(Player.id == r.player_id, Player.active.is_(True)).first()\n    if not player or player.suspended:\n        raise HTTPException(status_code=400, detail="Player is no longer eligible for this request.")\n\n    amount = payload.approved_xp or r.requested_xp\n    try:\n        transaction = award_xp(\n            db,\n            programme_id=player.programme_id,\n            player_id=player.id,\n            amount=amount,\n            group_amount=0,\n            transaction_type="point_request",\n            reason=f"Approved point request #{r.id}: {r.reason}",\n            reference_type="point_award_request",\n            reference_id=r.id,\n            created_by=user.id,\n        )\n        r.status = "approved"\n        r.reviewed_by = user.id\n        r.reviewed_at = datetime.utcnow()\n        r.review_note = payload.review_note\n        db.add(AuditLog(\n            user_id=user.id,\n            action="xp.point_request.approved",\n            entity_type="point_award_request",\n            entity_id=r.id,\n            details=f"player_id={player.id};requested={r.requested_xp};approved={amount};reason={r.reason}",\n        ))\n        db.commit()\n        db.refresh(r)\n        return {"success": True, "request": _serialize(r), "transaction_id": transaction.id, "approved_xp": amount}\n    except Exception as exc:\n        db.rollback()\n        raise HTTPException(status_code=400, detail=str(exc)) from exc\n\n\n@router.post("/{request_id}/reject")\ndef reject_request(\n    request_id: int,\n    payload: PointAwardDecision = PointAwardDecision(),\n    user=Depends(require_roles("admin", "youth_worker")),\n    db: Session = Depends(get_db),\n):\n    r = db.query(PointAwardRequest).filter(PointAwardRequest.id == request_id).first()\n    if not r:\n        raise HTTPException(status_code=404, detail="Point request not found.")\n    if r.status != "pending":\n        raise HTTPException(status_code=409, detail="This request has already been reviewed.")\n    r.status = "rejected"\n    r.reviewed_by = user.id\n    r.reviewed_at = datetime.utcnow()\n    r.review_note = payload.review_note or "Request declined by youth worker."\n    db.add(AuditLog(\n        user_id=user.id,\n        action="xp.point_request.rejected",\n        entity_type="point_award_request",\n        entity_id=r.id,\n        details=f"player_id={r.player_id};requested={r.requested_xp};reason={r.reason};note={r.review_note}",\n    ))\n    db.commit()\n    db.refresh(r)\n    return {"success": True, "request": _serialize(r)}\n')

# Register router in main.py.
main = ROOT / "app/main.py"
text = main.read_text()
if "points_requests" not in text:
    backup(main)

    # Handle the normal grouped-router import block.
    if "    reward_games,\n)" in text:
        text = text.replace(
            "    reward_games,\n)",
            "    reward_games,\n    points_requests,\n)",
            1,
        )
    elif "from .routers import (" in text:
        raise SystemExit("Could not safely extend router imports in app/main.py")
    else:
        text = text.replace(
            "from .routers import attendance",
            "from .routers import attendance\nfrom .routers import points_requests",
            1,
        )

    if "app.include_router(points_requests.router)" not in text:
        text = text.replace(
            "app.include_router(attendance.router)",
            "app.include_router(attendance.router)\napp.include_router(points_requests.router)",
            1,
        )

    main.write_text(text)

print("Backend point-request implementation applied.")
print("Restart FastAPI after this.")
