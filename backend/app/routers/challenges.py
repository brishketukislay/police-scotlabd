from __future__ import annotations
from app.services.gamification import get_active_programme

import secrets
from datetime import datetime, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..db.models.core import (
    AuditLog,
    Challenge,
    ChallengeAttempt,
    YouthGroup,
    Player,
)
from ..services.challenge_engine import (
    ChallengeError,
    ChallengeEndedError,
    ChallengeInactiveError,
    ChallengeNotFoundError,
    ChallengeNotStartedError,
    DuplicateChallengeAttemptError,
    InvalidChallengeScoreError,
    InvalidChallengeStateError,
    create_attempt,
    verify_attempt,
    reject_attempt,
    submit_attempt,
    finalise_attempt,
    challenge_summary,
    get_challenge,
)
from ..services.xp import player_xp


router = APIRouter(
    prefix="/api/challenges",
    tags=["challenges"],
)


UTC = timezone.utc


def utc_now() -> datetime:
    return datetime.now(UTC)


# ============================================================
# REQUEST MODELS
# ============================================================


class ChallengeAttemptRequest(BaseModel):
    """
    Public/player submission.

    The server decides whether the attempt is valid and how much XP
    it deserves.

    Never accept XP values from the client.
    """

    score: float = Field(
        ge=0,
        description="The verified game score.",
    )

    """
    Client-generated attempt identifier.

    This is not trusted as proof of performance. It exists to make a
    submission traceable and to support future idempotency.
    """

    attempt_id: str | None = Field(
        default=None,
        max_length=100,
    )

    """
    Optional client metadata.

    Do not put personal information here.

    Examples:

        {
            "game_version": "circle-v2",
            "duration_ms": 12000,
            "rounds": 5
        }
    """

    metadata: dict | None = None


class ChallengeCreateRequest(BaseModel):
    phase_id: int | None = None

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str | None = None

    start_at: datetime | None = None
    end_at: datetime | None = None

    participation_xp: int = Field(
        default=300,
        ge=0,
    )

    elite_xp: int = Field(
        default=1500,
        ge=0,
    )

    winner_xp: int = Field(
        default=3000,
        ge=0,
    )

    group_xp: int = Field(
        default=5000,
        ge=0,
    )

    active: bool = True


class ChallengeUpdateRequest(BaseModel):
    phase_id: int | None = None

    title: str = Field(
        min_length=1,
        max_length=200,
    )

    description: str | None = None

    start_at: datetime | None = None
    end_at: datetime | None = None

    participation_xp: int = Field(
        default=300,
        ge=0,
    )

    elite_xp: int = Field(
        default=1500,
        ge=0,
    )

    winner_xp: int = Field(
        default=3000,
        ge=0,
    )

    group_xp: int = Field(
        default=5000,
        ge=0,
    )

    active: bool = True


# ============================================================
# SERIALISATION
# ============================================================


def serialise_challenge(
    challenge: Challenge,
) -> dict:
    return {
        "id": challenge.id,
        "phase_id": challenge.phase_id,
        "title": challenge.title,
        "description": challenge.description,
        "start_at": challenge.start_at,
        "end_at": challenge.end_at,
        "participation_xp": challenge.participation_xp,
        "elite_xp": challenge.elite_xp,
        "winner_xp": challenge.winner_xp,
        "group_xp": challenge.group_xp,
        "active": challenge.active,
    }


# ============================================================
# PLAYER ENDPOINTS
# ============================================================


@router.get("")
def list_available_challenges(
    user=Depends(
        require_roles(
            "player",
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Return challenges that are currently relevant.

    Players receive only configuration necessary to participate.
    Staff can use the same endpoint during the current implementation;
    a richer staff reporting endpoint exists below.
    """

    now = utc_now()

    challenges = (
        db.query(Challenge)
        .filter(
            Challenge.active == True,
        )
        .order_by(
            Challenge.start_at.asc(),
            Challenge.id.asc(),
        )
        .all()
    )

    result = []

    for challenge in challenges:
        if challenge.start_at is not None:
            start_at = challenge.start_at

            if start_at.tzinfo is None:
                start_at = start_at.replace(
                    tzinfo=UTC,
                )

            if start_at > now:
                state = "scheduled"
            else:
                state = "live"
        else:
            state = "live"

        if challenge.end_at is not None:
            end_at = challenge.end_at

            if end_at.tzinfo is None:
                end_at = end_at.replace(
                    tzinfo=UTC,
                )

            if now > end_at:
                state = "ended"

        result.append(
            {
                **serialise_challenge(
                    challenge
                ),
                "state": state,
            }
        )

    return result



@router.get("/my-attempts")
def list_my_challenge_attempts(
    db: Session = Depends(get_db),
    current_user=Depends(require_roles("player")),
):
    """
    Return the authenticated player's challenge attempts.

    This is intentionally player-scoped and never accepts player_id
    from the client.
    """

    player = (
        db.query(Player)
        .filter(Player.user_id == current_user.id)
        .first()
    )

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player profile not found",
        )

    attempts = (
        db.query(ChallengeAttempt)
        .filter(
            ChallengeAttempt.player_id == player.id,
        )
        .order_by(ChallengeAttempt.id.desc())
        .all()
    )

    return {
        "attempts": [
            {
                "id": attempt.id,
                "challenge_id": attempt.challenge_id,
                "attempt_reference": attempt.attempt_reference,
                "status": attempt.status,
                "score": attempt.score,
                "percentile": attempt.percentile,
                "elite": attempt.elite,
                "winner": attempt.winner,
                "participation_xp": attempt.participation_xp,
                "elite_xp": attempt.elite_xp,
                "winner_xp": attempt.winner_xp,
                "individual_xp": attempt.individual_xp,
                "group_xp": attempt.group_xp,
                "submitted_at": attempt.submitted_at,
                "verified_at": attempt.verified_at,
                "rejection_reason": attempt.rejection_reason,
            }
            for attempt in attempts
        ]
    }


@router.get("/{challenge_id}")
def get_available_challenge(
    challenge_id: int,
    user=Depends(
        require_roles(
            "player",
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    try:
        challenge = get_challenge(
            db,
            challenge_id,
        )
    except ChallengeNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return serialise_challenge(
        challenge
    )


@router.get(
    "/staff/attempts/{attempt_id}",
)
def get_staff_challenge_attempt(
    attempt_id: int,
    user=Depends(
        require_roles("staff", "admin")
    ),
    db: Session = Depends(get_db),
):
    """
    Return the complete review payload for a single challenge attempt.

    Staff/admin users can use this endpoint to inspect the submitted
    score, evidence, workflow state, reward calculation, and verification
    metadata before deciding whether to verify or reject the attempt.
    """

    attempt = (
        db.query(ChallengeAttempt)
        .filter(
            ChallengeAttempt.id == attempt_id,
        )
        .first()
    )

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Challenge attempt not found",
        )

    challenge = (
        db.query(Challenge)
        .filter(
            Challenge.id == attempt.challenge_id,
        )
        .first()
    )

    player = (
        db.query(Player)
        .filter(
            Player.id == attempt.player_id,
        )
        .first()
    )

    return {
        "id": attempt.id,
        "challenge": {
            "id": challenge.id if challenge else attempt.challenge_id,
            "title": challenge.title if challenge else None,
        },
        "player": {
            "id": player.id if player else attempt.player_id,
            "user_id": player.user_id if player else None,
        },
        "attempt": {
            "attempt_number": attempt.attempt_number,
            "attempt_reference": attempt.attempt_reference,
            "status": attempt.status,
            "score": attempt.score,
            "percentile": attempt.percentile,
            "performance_percentile": (
                attempt.performance_percentile
            ),
            "submitted_at": (
                attempt.submitted_at.isoformat()
                if attempt.submitted_at
                else None
            ),
        },
        "evidence": {
            "type": attempt.evidence_type,
            "payload": attempt.evidence_payload,
            "hash": attempt.evidence_hash,
        },
        "review": {
            "verified": attempt.verified,
            "verified_by": attempt.verified_by,
            "verified_at": (
                attempt.verified_at.isoformat()
                if attempt.verified_at
                else None
            ),
            "rejection_reason": attempt.rejection_reason,
        },
        "achievement": {
            "participation_awarded": (
                attempt.participation_awarded
            ),
            "elite_awarded": attempt.elite_awarded,
            "winner_awarded": attempt.winner_awarded,
            "elite": attempt.elite,
            "winner": attempt.winner,
        },
        "xp": {
            "participation": attempt.participation_xp,
            "elite": attempt.elite_xp,
            "winner": attempt.winner_xp,
            "individual": attempt.individual_xp,
            "group": attempt.group_xp,
        },
    }


@router.post(
    "/{challenge_id}/attempt",
    status_code=status.HTTP_201_CREATED,
)
def submit_challenge_attempt(
    challenge_id: int,
    data: ChallengeAttemptRequest,
    user=Depends(
        require_roles("player")
    ),
    db: Session = Depends(get_db),
):
    """
    Submit a challenge attempt.

    The client supplies only the result/evidence.
    XP and achievement status are calculated by the server.
    """

    challenge = db.get(
        Challenge,
        challenge_id,
    )

    if not challenge:
        raise HTTPException(
            status_code=404,
            detail="Challenge not found",
        )

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
            status_code=403,
            detail="Active player profile not found",
        )

    attempt_reference = (
        data.attempt_id
        or secrets.token_urlsafe(16)
    )

    try:
        attempt = create_attempt(
            db,
            challenge=challenge,
            player=player,
            attempt_reference=attempt_reference,
            client_metadata=data.metadata,
        )

        attempt = submit_attempt(
            db,
            attempt=attempt,
            score=data.score,
            evidence_type="game_result",
            evidence_payload=data.metadata,
        )

        result = finalise_attempt(
            db,
            attempt=attempt,
            created_by=user.id,
        )

        # Submission itself is auditable. Rewarding is separately
        # recorded by the challenge engine.
        audit = AuditLog(
            user_id=user.id,
            action="challenge.submitted",
            entity_type="challenge_attempt",
            entity_id=attempt.id,
            details=(
                f"challenge_id={challenge.id};"
                f"player_id={player.id};"
                f"score={attempt.score}"
            ),
        )
        db.add(audit)

        db.commit()

    except (
        ChallengeInactiveError,
        ChallengeNotStartedError,
        ChallengeEndedError,
        InvalidChallengeScoreError,
        DuplicateChallengeAttemptError,
        InvalidChallengeStateError,
    ) as exc:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except ChallengeError as exc:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "success": True,
        "challenge": {
            "id": challenge.id,
            "title": challenge.title,
        },
        "attempt": {
            "id": result.attempt_id,
            "reference": result.attempt_reference,
            "status": result.status,
            "score": result.score,
        },
        "achievement": {
            "participation": True,
            "elite": result.elite,
            "winner": result.winner,
        },
        "xp": {
            "individual": result.individual_xp,
            "group": result.group_xp,
            "participation": result.participation_xp,
            "elite": result.elite_xp,
            "winner": result.winner_xp,
        },
        "player_total_xp": player_xp(
            db,
            player.id,
        ),
    }




@router.get(
    "/staff/audit",
)
def staff_list_challenge_audit(
    action: str | None = None,
    entity_type: str | None = None,
    entity_id: int | None = None,
    limit: int = 100,
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    """Return challenge-related audit events for authorised staff."""

    limit = max(min(limit, 500), 1)

    query = (
        db.query(AuditLog)
        .filter(
            AuditLog.entity_type == "challenge_attempt",
        )
    )

    if action is not None:
        query = query.filter(
            AuditLog.action == action,
        )

    if entity_type is not None:
        query = query.filter(
            AuditLog.entity_type == entity_type,
        )

    if entity_id is not None:
        query = query.filter(
            AuditLog.entity_id == entity_id,
        )

    entries = (
        query
        .order_by(
            AuditLog.id.desc(),
        )
        .limit(limit)
        .all()
    )

    return [
        {
            "id": entry.id,
            "user_id": entry.user_id,
            "action": entry.action,
            "entity_type": entry.entity_type,
            "entity_id": entry.entity_id,
            "details": entry.details,
            "created_at": (
                entry.created_at.isoformat()
                if entry.created_at
                else None
            ),
        }
        for entry in entries
    ]

@router.get(
    "/staff/attempts",
)
def staff_list_attempts(
    status: str | None = None,
    challenge_id: int | None = None,
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Return challenge attempts for staff review.

    By default this returns submitted attempts first, followed by
    verified/rejected attempts. Staff can filter by status and challenge.

    Player identity is intentionally limited to the player profile fields
    needed by staff to identify the participant.
    """

    query = (
        db.query(ChallengeAttempt)
        .join(
            Challenge,
            Challenge.id == ChallengeAttempt.challenge_id,
        )
    )

    if status is not None:
        allowed_statuses = {
            "created",
            "submitted",
            "verified",
            "rejected",
        }

        if status not in allowed_statuses:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Invalid attempt status. "
                    "Expected one of: "
                    + ", ".join(sorted(allowed_statuses))
                ),
            )

        query = query.filter(
            ChallengeAttempt.status == status,
        )

    if challenge_id is not None:
        query = query.filter(
            ChallengeAttempt.challenge_id == challenge_id,
        )

    attempts = (
        query
        .order_by(
            ChallengeAttempt.submitted_at.desc(),
            ChallengeAttempt.id.desc(),
        )
        .all()
    )

    return [
        {
            "id": attempt.id,
            "challenge_id": attempt.challenge_id,
            "challenge_title": (
                attempt.challenge.title
                if attempt.challenge is not None
                else None
            ),
            "player_id": attempt.player_id,
            "gamertag": (
                attempt.player.gamertag
                if attempt.player is not None
                else None
            ),
            "attempt_number": attempt.attempt_number,
            "attempt_reference": attempt.attempt_reference,
            "score": attempt.score,
            "status": attempt.status,
            "evidence_type": attempt.evidence_type,
            "evidence_payload": attempt.evidence_payload,
            "submitted_at": attempt.submitted_at,
            "verified_by": attempt.verified_by,
            "verified_at": attempt.verified_at,
            "rejection_reason": attempt.rejection_reason,
            "percentile": attempt.percentile,
            "elite": attempt.elite,
            "winner": attempt.winner,
            "participation_xp": attempt.participation_xp,
            "elite_xp": attempt.elite_xp,
            "winner_xp": attempt.winner_xp,
            "individual_xp": attempt.individual_xp,
            "group_xp": attempt.group_xp,
        }
        for attempt in attempts
    ]


@router.post(
    "/staff/attempts/{attempt_id}/verify",
)
def staff_verify_attempt(
    attempt_id: int,
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Verify a submitted challenge attempt and award XP.

    The challenge engine remains the single authority for calculating
    percentile, elite/winner status and XP.
    """

    attempt = db.get(
        ChallengeAttempt,
        attempt_id,
    )

    if attempt is None:
        raise HTTPException(
            status_code=404,
            detail="Challenge attempt not found",
        )

    try:
        result = verify_attempt(
            db,
            attempt=attempt,
            verified_by=user.id,
        )

        db.commit()

    except InvalidChallengeStateError as exc:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except ChallengeError as exc:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "success": True,
        "attempt": {
            "id": attempt.id,
            "reference": attempt.attempt_reference,
            "status": attempt.status,
            "score": attempt.score,
        },
        "achievement": {
            "elite": result.elite,
            "winner": result.winner,
        },
        "xp": {
            "individual": result.individual_xp,
            "group": result.group_xp,
            "participation": result.participation_xp,
            "elite": result.elite_xp,
            "winner": result.winner_xp,
        },
        "percentile": result.percentile,
    }


class ChallengeAttemptRejectRequest(BaseModel):
    reason: str = Field(
        min_length=1,
        max_length=1000,
    )


@router.post(
    "/staff/attempts/{attempt_id}/reject",
)
def staff_reject_attempt(
    attempt_id: int,
    data: ChallengeAttemptRejectRequest,
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Reject a submitted challenge attempt.

    Rejection never awards XP.
    """

    attempt = db.get(
        ChallengeAttempt,
        attempt_id,
    )

    if attempt is None:
        raise HTTPException(
            status_code=404,
            detail="Challenge attempt not found",
        )

    try:
        attempt = reject_attempt(
            db,
            attempt=attempt,
            reason=data.reason.strip(),
            verified_by=user.id,
        )

        db.commit()

    except InvalidChallengeStateError as exc:
        db.rollback()

        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except ChallengeError as exc:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    return {
        "success": True,
        "attempt": {
            "id": attempt.id,
            "reference": attempt.attempt_reference,
            "status": attempt.status,
            "score": attempt.score,
        },
        "rejection_reason": attempt.rejection_reason,
        "verified_by": attempt.verified_by,
        "verified_at": attempt.verified_at,
    }


# ============================================================
# STAFF ENDPOINTS
# ============================================================


@router.get(
    "/staff/list",
)
def staff_list_challenges(
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Staff view.

    This intentionally returns inactive and historical challenges as
    well as live challenges so administrators can manage the complete
    challenge catalogue.
    """

    challenges = (
        db.query(Challenge)
        .order_by(
            Challenge.start_at.desc(),
            Challenge.id.desc(),
        )
        .all()
    )

    return [
        {
            **serialise_challenge(
                challenge
            ),
            "summary": challenge_summary(
                db,
                challenge,
            ),
        }
        for challenge in challenges
    ]


@router.post(
    "/staff",
    status_code=status.HTTP_201_CREATED,
)
def create_challenge(
    data: ChallengeCreateRequest,
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    if (
        data.start_at is not None
        and data.end_at is not None
        and data.end_at <= data.start_at
    ):
        raise HTTPException(
            status_code=400,
            detail="Challenge end time must be after its start time.",
        )

    programme = get_active_programme(db)

    challenge = Challenge(
        programme_id=programme.id,
        phase_id=data.phase_id,
        title=data.title.strip(),
        description=data.description,
        start_at=data.start_at,
        end_at=data.end_at,
        participation_xp=data.participation_xp,
        elite_xp=data.elite_xp,
        winner_xp=data.winner_xp,
        group_xp=data.group_xp,
        active=data.active,
    )

    db.add(challenge)
    db.commit()
    db.refresh(challenge)

    return serialise_challenge(
        challenge
    )


@router.put(
    "/staff/{challenge_id}",
)
def update_challenge(
    challenge_id: int,
    data: ChallengeUpdateRequest,
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    challenge = db.get(
        Challenge,
        challenge_id,
    )

    if not challenge:
        raise HTTPException(
            status_code=404,
            detail="Challenge not found",
        )

    if (
        data.start_at is not None
        and data.end_at is not None
        and data.end_at <= data.start_at
    ):
        raise HTTPException(
            status_code=400,
            detail="Challenge end time must be after its start time.",
        )

    challenge.phase_id = data.phase_id
    challenge.title = data.title.strip()
    challenge.description = data.description
    challenge.start_at = data.start_at
    challenge.end_at = data.end_at
    challenge.participation_xp = data.participation_xp
    challenge.elite_xp = data.elite_xp
    challenge.winner_xp = data.winner_xp
    challenge.group_xp = data.group_xp
    challenge.active = data.active

    db.commit()
    db.refresh(challenge)

    return serialise_challenge(
        challenge
    )


@router.post(
    "/staff/{challenge_id}/enable",
)
def enable_challenge(
    challenge_id: int,
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    challenge = db.get(
        Challenge,
        challenge_id,
    )

    if not challenge:
        raise HTTPException(
            status_code=404,
            detail="Challenge not found",
        )

    challenge.active = True

    db.commit()

    return {
        "success": True,
        "id": challenge.id,
        "active": True,
    }


@router.post(
    "/staff/{challenge_id}/disable",
)
def disable_challenge(
    challenge_id: int,
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    challenge = db.get(
        Challenge,
        challenge_id,
    )

    if not challenge:
        raise HTTPException(
            status_code=404,
            detail="Challenge not found",
        )

    challenge.active = False

    db.commit()

    return {
        "success": True,
        "id": challenge.id,
        "active": False,
    }
