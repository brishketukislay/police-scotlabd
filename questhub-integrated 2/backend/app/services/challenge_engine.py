from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.orm import Session

from ..db.models.core import (
    AuditLog,
    Challenge,
    ChallengeAttempt,
    Player,
)
from .xp import award_xp


UTC = timezone.utc


class ChallengeAttemptStatus(str, Enum):
    CREATED = "created"
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ChallengeError(Exception):
    """Base challenge-domain exception."""


class ChallengeNotFoundError(ChallengeError):
    pass


class ChallengeInactiveError(ChallengeError):
    pass


class ChallengeNotStartedError(ChallengeError):
    pass


class ChallengeEndedError(ChallengeError):
    pass


class InvalidChallengeScoreError(ChallengeError):
    pass


class DuplicateChallengeAttemptError(ChallengeError):
    pass


class InvalidChallengeStateError(ChallengeError):
    pass


@dataclass(frozen=True)
class ChallengeResult:
    challenge_id: int
    player_id: int
    attempt_id: int
    attempt_reference: str

    score: float
    percentile: float | None

    participation_xp: int
    elite_xp: int
    winner_xp: int

    individual_xp: int
    group_xp: int

    elite: bool
    winner: bool

    status: str


@dataclass(frozen=True)
class ChallengeConfiguration:
    participation_xp: int
    elite_xp: int
    winner_xp: int
    group_xp: int

    elite_percentile: float
    max_attempts_per_player: int

    requires_verification: bool
    scoring_direction: str

    @classmethod
    def from_model(
        cls,
        challenge: Challenge,
    ) -> "ChallengeConfiguration":
        direction = (
            challenge.scoring_direction
            or "higher"
        ).lower()

        if direction not in {
            "higher",
            "lower",
        }:
            direction = "higher"

        return cls(
            participation_xp=max(
                int(challenge.participation_xp or 0),
                0,
            ),
            elite_xp=max(
                int(challenge.elite_xp or 0),
                0,
            ),
            winner_xp=max(
                int(challenge.winner_xp or 0),
                0,
            ),
            group_xp=max(
                int(challenge.group_xp or 0),
                0,
            ),
            elite_percentile=min(
                max(
                    float(
                        challenge.elite_percentile
                        or 90.0
                    ),
                    0.0,
                ),
                100.0,
            ),
            max_attempts_per_player=max(
                int(
                    challenge.max_attempts_per_player
                    or 0
                ),
                0,
            ),
            requires_verification=bool(
                challenge.requires_verification
            ),
            scoring_direction=direction,
        )


def utc_now() -> datetime:
    return datetime.now(UTC)


def write_challenge_audit(
    db: Session,
    *,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | None,
    details: str | None = None,
) -> AuditLog:
    """
    Record a challenge-domain audit event.

    The helper deliberately does not commit. The caller owns the
    surrounding database transaction.
    """

    entry = AuditLog(
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        details=details,
    )

    db.add(entry)
    db.flush()

    return entry


def get_challenge(
    db: Session,
    challenge_id: int,
) -> Challenge:
    challenge = db.get(
        Challenge,
        challenge_id,
    )

    if challenge is None:
        raise ChallengeNotFoundError(
            f"Challenge {challenge_id} was not found."
        )

    return challenge


def normalise_datetime(
    value: datetime | None,
) -> datetime | None:
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(
            tzinfo=UTC
        )

    return value


def validate_challenge_window(
    challenge: Challenge,
    now: datetime | None = None,
) -> None:
    current_time = now or utc_now()

    if not challenge.active:
        raise ChallengeInactiveError(
            "This challenge is not active."
        )

    start_at = normalise_datetime(
        challenge.start_at
    )

    end_at = normalise_datetime(
        challenge.end_at
    )

    if (
        start_at is not None
        and current_time < start_at
    ):
        raise ChallengeNotStartedError(
            "This challenge has not started yet."
        )

    if (
        end_at is not None
        and current_time > end_at
    ):
        raise ChallengeEndedError(
            "This challenge has ended."
        )


def validate_score(
    score: float,
) -> float:
    try:
        value = float(score)
    except (
        TypeError,
        ValueError,
    ) as exc:
        raise InvalidChallengeScoreError(
            "Score must be a valid number."
        ) from exc

    if value != value:
        raise InvalidChallengeScoreError(
            "Score cannot be NaN."
        )

    if value in (
        float("inf"),
        float("-inf"),
    ):
        raise InvalidChallengeScoreError(
            "Score must be finite."
        )

    if value < 0:
        raise InvalidChallengeScoreError(
            "Score cannot be negative."
        )

    return value


def get_player_attempt_count(
    db: Session,
    challenge_id: int,
    player_id: int,
) -> int:
    return (
        db.query(ChallengeAttempt)
        .filter(
            ChallengeAttempt.challenge_id
            == challenge_id,
            ChallengeAttempt.player_id
            == player_id,
            ChallengeAttempt.status
            != ChallengeAttemptStatus.REJECTED.value,
        )
        .count()
    )


def get_attempt_by_reference(
    db: Session,
    attempt_reference: str,
) -> ChallengeAttempt | None:
    return (
        db.query(ChallengeAttempt)
        .filter(
            ChallengeAttempt.attempt_reference
            == attempt_reference,
        )
        .first()
    )


def get_submitted_scores(
    db: Session,
    challenge_id: int,
    *,
    exclude_attempt_id: int | None = None,
) -> list[float]:
    query = (
        db.query(
            ChallengeAttempt.score
        )
        .filter(
            ChallengeAttempt.challenge_id
            == challenge_id,
            ChallengeAttempt.score.isnot(None),
            ChallengeAttempt.status.in_(
                [
                    ChallengeAttemptStatus.SUBMITTED.value,
                    ChallengeAttemptStatus.VERIFIED.value,
                ]
            ),
        )
    )

    if exclude_attempt_id is not None:
        query = query.filter(
            ChallengeAttempt.id
            != exclude_attempt_id
        )

    return [
        float(row[0])
        for row in query.all()
        if row[0] is not None
    ]


def calculate_percentile(
    score: float,
    scores: list[float],
    scoring_direction: str,
) -> float:
    """
    Calculate the participant's percentile among submitted scores.

    Higher is better:
        90 means the score is around the top 10%.

    Lower is better:
        90 means the score is around the best 10%.

    The function uses <= / >= semantics rather than assigning an
    arbitrary rank to tied players.
    """

    if not scores:
        return 100.0

    direction = scoring_direction.lower()

    if direction == "lower":
        better_or_equal = sum(
            value >= score
            for value in scores
        )
    else:
        better_or_equal = sum(
            value <= score
            for value in scores
        )

    percentile = (
        better_or_equal
        / len(scores)
    ) * 100

    return round(
        min(
            max(percentile, 0.0),
            100.0,
        ),
        2,
    )


def determine_elite(
    percentile: float,
    threshold: float,
) -> bool:
    return percentile >= threshold


def determine_winner(
    score: float,
    scores: list[float],
    scoring_direction: str,
) -> bool:
    if not scores:
        return True

    if scoring_direction == "lower":
        return score <= min(scores)

    return score >= max(scores)


def build_challenge_result(
    challenge: Challenge,
    player: Player,
    attempt: ChallengeAttempt,
    percentile: float,
    winner: bool,
) -> ChallengeResult:
    configuration = (
        ChallengeConfiguration.from_model(
            challenge
        )
    )

    elite = determine_elite(
        percentile,
        configuration.elite_percentile,
    )

    participation_xp = (
        configuration.participation_xp
    )

    elite_xp = (
        configuration.elite_xp
        if elite
        else 0
    )

    winner_xp = (
        configuration.winner_xp
        if winner
        else 0
    )

    individual_xp = (
        participation_xp
        + elite_xp
        + winner_xp
    )

    group_xp = (
        configuration.group_xp
        if winner
        else 0
    )

    return ChallengeResult(
        challenge_id=challenge.id,
        player_id=player.id,
        attempt_id=attempt.id,
        attempt_reference=attempt.attempt_reference,
        score=float(attempt.score or 0),
        percentile=percentile,
        participation_xp=participation_xp,
        elite_xp=elite_xp,
        winner_xp=winner_xp,
        individual_xp=individual_xp,
        group_xp=group_xp,
        elite=elite,
        winner=winner,
        status=attempt.status,
    )


def create_attempt(
    db: Session,
    *,
    challenge: Challenge,
    player: Player,
    attempt_reference: str,
    client_metadata: dict[str, Any] | None = None,
) -> ChallengeAttempt:
    """
    Create a server-side attempt record.

    `attempt_reference` is the idempotency key for the client operation.

    If the reference already exists for the same player/challenge,
    the existing attempt is returned. The router can then determine
    whether this is a completed retry or an attempt that still needs
    submission.
    """

    if not attempt_reference or not attempt_reference.strip():
        raise DuplicateChallengeAttemptError(
            "attempt_reference is required."
        )

    attempt_reference = attempt_reference.strip()

    existing = get_attempt_by_reference(
        db,
        attempt_reference,
    )

    if existing is not None:
        if (
            existing.challenge_id != challenge.id
            or existing.player_id != player.id
        ):
            raise DuplicateChallengeAttemptError(
                "This attempt reference belongs to another challenge or player."
            )

        return existing

    validate_challenge_window(challenge)

    if not player.active:
        raise ChallengeError(
            "Inactive players cannot participate."
        )

    configuration = ChallengeConfiguration.from_model(challenge)

    current_attempts = get_player_attempt_count(
        db,
        challenge.id,
        player.id,
    )

    if (
        configuration.max_attempts_per_player > 0
        and current_attempts >= configuration.max_attempts_per_player
    ):
        raise DuplicateChallengeAttemptError(
            "Maximum attempts reached."
        )

    attempt = ChallengeAttempt(
        challenge_id=challenge.id,
        player_id=player.id,
        attempt_reference=attempt_reference,
        status=ChallengeAttemptStatus.CREATED.value,
        client_metadata=client_metadata,
    )

    db.add(attempt)
    db.flush()

    return attempt



def submit_attempt(
    db: Session,
    *,
    attempt: ChallengeAttempt,
    score: float,
    evidence_type: str = "game_result",
    evidence_payload: dict[str, Any] | None = None,
) -> ChallengeAttempt:
    """
    Move a created attempt to submitted state.

    A retry of an already-submitted/verified attempt is treated as an
    idempotent operation only when the supplied score matches the
    persisted score.

    A different score is rejected so a client cannot silently mutate
    an already-submitted result.
    """

    validated_score = validate_score(score)

    if attempt.status in {
        ChallengeAttemptStatus.SUBMITTED.value,
        ChallengeAttemptStatus.VERIFIED.value,
    }:
        if attempt.score is None:
            raise InvalidChallengeStateError(
                "This attempt is already submitted but has no score."
            )

        if float(attempt.score) != validated_score:
            raise InvalidChallengeStateError(
                "This attempt has already been submitted with a different score."
            )

        return attempt

    if attempt.status == ChallengeAttemptStatus.REJECTED.value:
        raise InvalidChallengeStateError(
            "A rejected attempt cannot be resubmitted."
        )

    if attempt.status != ChallengeAttemptStatus.CREATED.value:
        raise InvalidChallengeStateError(
            "This attempt cannot be submitted."
        )

    attempt.score = validated_score
    attempt.evidence_type = evidence_type
    attempt.evidence_payload = evidence_payload
    attempt.submitted_at = utc_now()
    attempt.status = ChallengeAttemptStatus.SUBMITTED.value

    db.flush()

    return attempt



def finalise_attempt(
    db: Session,
    *,
    attempt: ChallengeAttempt,
    created_by: int | None = None,
) -> ChallengeResult:
    """
    Calculate and persist the reward for a submitted attempt.

    This function is deliberately the only place where challenge
    performance becomes challenge XP.
    """

    if attempt.status not in {
        ChallengeAttemptStatus.SUBMITTED.value,
        ChallengeAttemptStatus.VERIFIED.value,
    }:
        raise InvalidChallengeStateError(
            "Only submitted or verified attempts can be finalised."
        )

    challenge = attempt.challenge
    player = attempt.player

    if attempt.score is None:
        raise InvalidChallengeScoreError(
            "Attempt has no score."
        )

    configuration = (
        ChallengeConfiguration.from_model(
            challenge
        )
    )

    other_scores = get_submitted_scores(
        db,
        challenge.id,
        exclude_attempt_id=attempt.id,
    )

    percentile = calculate_percentile(
        float(attempt.score),
        other_scores,
        configuration.scoring_direction,
    )

    winner = determine_winner(
        float(attempt.score),
        other_scores,
        configuration.scoring_direction,
    )

    result = build_challenge_result(
        challenge,
        player,
        attempt,
        percentile,
        winner,
    )

    # --------------------------------------------------------
    # Verification gate
    # --------------------------------------------------------

    if (
        configuration.requires_verification
        and attempt.status
        != ChallengeAttemptStatus.VERIFIED.value
    ):
        return result

    # --------------------------------------------------------
    # Prevent duplicate XP
    # --------------------------------------------------------
    #
    # XP values may legitimately be zero. Therefore the reward
    # amount itself must never be used as the idempotency check.
    #
    # `participation_awarded` is the persisted marker that says
    # this attempt has already gone through reward finalisation.
    #

    if attempt.participation_awarded:
        return result

    attempt.percentile = result.percentile
    attempt.elite = result.elite
    attempt.winner = result.winner

    attempt.participation_xp = (
        result.participation_xp
    )
    attempt.elite_xp = result.elite_xp
    attempt.winner_xp = (
        result.winner_xp
    )
    attempt.individual_xp = (
        result.individual_xp
    )
    attempt.group_xp = result.group_xp

    # Keep the legacy persisted state fields aligned with the
    # canonical workflow state.
    attempt.performance_percentile = (
        result.percentile
    )
    attempt.participation_awarded = (
        result.participation_xp > 0
    )
    attempt.elite_awarded = (
        result.elite_xp > 0
    )
    attempt.winner_awarded = (
        result.winner_xp > 0
    )

    award_xp(
        db=db,
        programme_id=challenge.programme_id,
        player_id=player.id,
        amount=result.individual_xp,
        group_amount=result.group_xp,
        transaction_type="challenge",
        reason=(
            f"Challenge '{challenge.title}' "
            f"attempt {attempt.attempt_reference}"
        ),
        reference_type="challenge_attempt",
        reference_id=attempt.id,
        created_by=created_by,
    )

    # The reward transaction has now been created successfully.
    # This is the canonical idempotency marker for the attempt.
    attempt.participation_awarded = True

    write_challenge_audit(
        db,
        user_id=created_by,
        action="challenge.rewarded",
        entity_type="challenge_attempt",
        entity_id=attempt.id,
        details=(
            f"challenge_id={challenge.id};"
            f"player_id={player.id};"
            f"individual_xp={result.individual_xp};"
            f"group_xp={result.group_xp};"
            f"elite={result.elite};"
            f"winner={result.winner}"
        ),
    )

    if attempt.status != ChallengeAttemptStatus.VERIFIED.value:
        attempt.status = (
            ChallengeAttemptStatus.VERIFIED.value
            if configuration.requires_verification
            else ChallengeAttemptStatus.SUBMITTED.value
        )

    db.flush()

    return result


def reject_attempt(
    db: Session,
    *,
    attempt: ChallengeAttempt,
    reason: str,
    verified_by: int,
) -> ChallengeAttempt:
    if attempt.status in {
        ChallengeAttemptStatus.VERIFIED.value,
    }:
        raise InvalidChallengeStateError(
            "A verified attempt cannot be rejected."
        )

    attempt.status = (
        ChallengeAttemptStatus.REJECTED.value
    )

    # Rejected attempts are never verified and never receive XP.
    attempt.verified = False

    attempt.rejection_reason = reason
    attempt.verified_by = verified_by
    attempt.verified_at = utc_now()

    write_challenge_audit(
        db,
        user_id=verified_by,
        action="challenge.rejected",
        entity_type="challenge_attempt",
        entity_id=attempt.id,
        details=(
            f"challenge_id={attempt.challenge_id};"
            f"player_id={attempt.player_id};"
            f"reason={reason.strip()}"
        ),
    )

    db.flush()

    return attempt


def verify_attempt(
    db: Session,
    *,
    attempt: ChallengeAttempt,
    verified_by: int,
) -> ChallengeResult:
    """
    Staff verification path.

    Verification is intentionally separate from submission because
    some activities may require a youth worker to confirm the result.
    """

    if attempt.status != (
        ChallengeAttemptStatus.SUBMITTED.value
    ):
        raise InvalidChallengeStateError(
            "Only submitted attempts can be verified."
        )

    attempt.status = (
        ChallengeAttemptStatus.VERIFIED.value
    )

    # Keep the legacy verification flag synchronized while the
    # database still contains both representations.
    attempt.verified = True

    attempt.verified_by = verified_by
    attempt.verified_at = utc_now()

    write_challenge_audit(
        db,
        user_id=verified_by,
        action="challenge.verified",
        entity_type="challenge_attempt",
        entity_id=attempt.id,
        details=(
            f"challenge_id={attempt.challenge_id};"
            f"player_id={attempt.player_id}"
        ),
    )

    db.flush()

    return finalise_attempt(
        db,
        attempt=attempt,
        created_by=verified_by,
    )


def challenge_summary(
    db: Session,
    challenge: Challenge,
) -> dict[str, Any]:
    attempts = (
        db.query(ChallengeAttempt)
        .filter(
            ChallengeAttempt.challenge_id
            == challenge.id,
        )
        .all()
    )

    submitted = [
        attempt
        for attempt in attempts
        if attempt.score is not None
        and attempt.status
        in {
            ChallengeAttemptStatus.SUBMITTED.value,
            ChallengeAttemptStatus.VERIFIED.value,
        }
    ]

    individual_xp = sum(
        attempt.individual_xp
        for attempt in attempts
    )

    group_xp = sum(
        attempt.group_xp
        for attempt in attempts
    )

    return {
        "challenge_id": challenge.id,
        "title": challenge.title,
        "game_type": challenge.game_type,
        "active": challenge.active,
        "attempts": len(attempts),
        "submitted_attempts": len(submitted),
        "verified_attempts": sum(
            attempt.status
            == ChallengeAttemptStatus.VERIFIED.value
            for attempt in attempts
        ),
        "rejected_attempts": sum(
            attempt.status
            == ChallengeAttemptStatus.REJECTED.value
            for attempt in attempts
        ),
        "individual_xp_awarded": individual_xp,
        "group_xp_awarded": group_xp,
    }
