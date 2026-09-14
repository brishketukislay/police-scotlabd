from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..db.database import get_db
from ..db.models import (
    Player,
    PlayerRewardGame,
    Programme,
    RewardGame,
    RewardGamePlayStatus,
    RewardGameType,
)
from ..services.xp import award_xp


router = APIRouter(
    prefix="/api/reward-games",
    tags=["reward-games"],
)


def normalise_datetime(value: datetime | None) -> datetime | None:
    """
    Normalise an incoming datetime to UTC and remove tzinfo before storing
    it in the existing timezone-naive SQLAlchemy DateTime column.
    """
    if value is None:
        return None

    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    else:
        value = value.astimezone(timezone.utc)

    return value.replace(tzinfo=None)



def comparison_datetime(value: datetime | None) -> datetime | None:
    """
    Convert database datetime values to timezone-aware UTC datetimes.

    SQLite/SQLAlchemy may return DateTime columns without tzinfo, while
    browser/API input may contain timezone-aware ISO timestamps.
    """
    if value is None:
        return None

    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)

    return value.astimezone(timezone.utc)



def now_utc() -> datetime:
    return datetime.now(timezone.utc)


def game_is_live(game: RewardGame, now: datetime) -> bool:
    if not game.active:
        return False

    if game.starts_at and now < comparison_datetime(game.starts_at):
        return False

    if game.ends_at and now >= comparison_datetime(game.ends_at):
        return False

    return True


def game_is_upcoming(game: RewardGame, now: datetime) -> bool:
    if not game.active:
        return False

    if not game.show_upcoming:
        return False

    if game.starts_at and now < comparison_datetime(game.starts_at):
        return True

    return False


def validate_prizes(values: list[int]) -> list[int]:
    cleaned = sorted(
        {
            int(value)
            for value in values
            if int(value) >= 0
        }
    )

    if not cleaned:
        raise HTTPException(
            status_code=400,
            detail="At least one prize value is required.",
        )

    if len(cleaned) > 20:
        raise HTTPException(
            status_code=400,
            detail="A game can contain at most 20 prize values.",
        )

    return cleaned


class RewardGameCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    game_type: RewardGameType

    prize_values: list[int] = Field(
        ...,
        min_length=1,
        max_length=20,
    )

    starts_at: datetime | None = None
    ends_at: datetime | None = None

    active: bool = True
    show_upcoming: bool = True


class GrantRewardGameRequest(BaseModel):
    player_id: int


class PlayResponse(BaseModel):
    success: bool
    play_id: int
    game_id: int
    game_type: str
    awarded_xp: int
    player_total_xp: int


def serialize_game(
    game: RewardGame,
    now: datetime | None = None,
):
    now = now or now_utc()

    if game_is_live(game, now):
        state = "available"
    elif game_is_upcoming(game, now):
        state = "upcoming"
    else:
        state = "inactive"

    return {
        "id": game.id,
        "name": game.name,
        "description": game.description,
        "game_type": game.game_type.value,
        "prize_values": game.prize_values,
        "starts_at": game.starts_at,
        "ends_at": game.ends_at,
        "active": game.active,
        "show_upcoming": game.show_upcoming,
        "state": state,
    }


# ---------------------------------------------------------------------------
# PLAYER
# ---------------------------------------------------------------------------

@router.get("/player")
def player_reward_games(
    user=Depends(require_roles("player")),
    db: Session = Depends(get_db),
):
    player = (
        db.query(Player)
        .filter(
            Player.user_id == user.id,
            Player.active.is_(True),
        )
        .first()
    )

    if not player:
        raise HTTPException(
            status_code=404,
            detail="Player profile not found.",
        )

    # Reward games are programme-level entitlements.
    # A player does NOT need to belong to a group to receive or see
    # a reward game. Use the player's programme directly.
    if player.programme_id is None:
        return {
            "available": [],
            "upcoming": [],
        }

    games = (
        db.query(RewardGame)
        .filter(
            RewardGame.programme_id
            == player.programme_id,
            RewardGame.active.is_(True),
        )
        .order_by(
            RewardGame.starts_at.asc(),
            RewardGame.id.asc(),
        )
        .all()
    )

    now = now_utc()

    available = []
    upcoming = []

    for game in games:
        # Only show games for which the player has an unused entitlement.
        entitlement = (
            db.query(PlayerRewardGame)
            .filter(
                PlayerRewardGame.game_id == game.id,
                PlayerRewardGame.player_id == player.id,
                PlayerRewardGame.status
                == RewardGamePlayStatus.AVAILABLE,
            )
            .first()
        )

        if not entitlement:
            continue

        payload = {
            **serialize_game(game, now),
            "play_id": entitlement.id,
        }

        if game_is_live(game, now):
            available.append(payload)
        elif game_is_upcoming(game, now):
            upcoming.append(payload)

    return {
        "available": available,
        "upcoming": upcoming,
    }


@router.post(
    "/{play_id}/play",
    response_model=PlayResponse,
)
def play_reward_game(
    play_id: int,
    user=Depends(require_roles("player")),
    db: Session = Depends(get_db),
):
    player = (
        db.query(Player)
        .filter(
            Player.user_id == user.id,
            Player.active.is_(True),
        )
        .first()
    )

    if not player:
        raise HTTPException(
            status_code=404,
            detail="Player profile not found.",
        )

    # SQLite cannot provide the same row-lock semantics as PostgreSQL,
    # so the entitlement is re-read inside the transaction and immediately
    # transitioned before awarding XP.
    play = (
        db.query(PlayerRewardGame)
        .filter(
            PlayerRewardGame.id == play_id,
            PlayerRewardGame.player_id == player.id,
        )
        .first()
    )

    if not play:
        raise HTTPException(
            status_code=404,
            detail="Reward game play not found.",
        )

    if play.status != RewardGamePlayStatus.AVAILABLE:
        raise HTTPException(
            status_code=409,
            detail="This reward has already been played.",
        )

    game = (
        db.query(RewardGame)
        .filter(
            RewardGame.id == play.game_id,
            RewardGame.active.is_(True),
        )
        .first()
    )

    if not game:
        raise HTTPException(
            status_code=404,
            detail="Reward game is no longer available.",
        )

    now = now_utc()

    if not game_is_live(game, now):
        raise HTTPException(
            status_code=409,
            detail="This reward game is not currently available.",
        )

    # Reward games are programme-level rewards.
    # A player does not need to be assigned to an active youth group.
    # The player's programme is sufficient for awarding the XP.

    if player.programme_id is None:
        raise HTTPException(
            status_code=400,
            detail="Player is not assigned to a programme.",
        )

    prizes = validate_prizes(game.prize_values)

    # Cryptographically secure server-side selection.
    awarded_xp = secrets.choice(prizes)

    play.status = RewardGamePlayStatus.PLAYED
    play.awarded_xp = awarded_xp
    play.played_at = now
    play.play_metadata = {
        "selection": "server",
        "game_type": game.game_type.value,
    }

    db.flush()
    # One play represents one logical reward entitlement.
    # The stable key prevents duplicate XP on request retries.
    idempotency_key = f"reward-game-play:{play.id}"


    try:
        transaction = award_xp(
            db,
            programme_id=player.programme_id,
            player_id=player.id,
            amount=awarded_xp,
            # No group is required for reward-game XP.
            group_amount=0,
            transaction_type=(
                "reward_game_scratch"
                if game.game_type == RewardGameType.SCRATCH
                else "reward_game_wheel"
            ),
            reason=(
                f"{game.name}: reward game result"
            ),
            reference_type="reward_game_play",
            reference_id=play.id,
            idempotency_key=idempotency_key,
            created_by=user.id,
        )

        play.xp_transaction_id = transaction.id

        db.commit()

    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="The reward could not be completed safely. Please retry.",
        ) from exc

    # player_xp is intentionally imported lazily to avoid circular imports.
    from ..services.xp import player_xp

    total = player_xp(
        db,
        player.id,
    )

    return PlayResponse(
        success=True,
        play_id=play.id,
        game_id=game.id,
        game_type=game.game_type.value,
        awarded_xp=awarded_xp,
        player_total_xp=total,
    )


# ---------------------------------------------------------------------------
# ADMIN
# ---------------------------------------------------------------------------

@router.get("/admin")
def admin_reward_games(
    user=Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    programme = (
        db.query(RewardGame.programme_id)
        .filter(
            RewardGame.active.is_(True)
        )
        .first()
    )

    if not programme:
        return []

    programme_id = programme[0]

    games = (
        db.query(RewardGame)
        .filter(
            RewardGame.programme_id == programme_id,
        )
        .order_by(
            RewardGame.starts_at.desc(),
            RewardGame.id.desc(),
        )
        .all()
    )

    result = []

    for game in games:
        available = (
            db.query(PlayerRewardGame)
            .filter(
                PlayerRewardGame.game_id == game.id,
                PlayerRewardGame.status
                == RewardGamePlayStatus.AVAILABLE,
            )
            .count()
        )

        played = (
            db.query(PlayerRewardGame)
            .filter(
                PlayerRewardGame.game_id == game.id,
                PlayerRewardGame.status
                == RewardGamePlayStatus.PLAYED,
            )
            .count()
        )

        result.append(
            {
                **serialize_game(game),
                "available_entitlements": available,
                "played_entitlements": played,
            }
        )

    return result


@router.post("/admin")
def create_reward_game(
    data: RewardGameCreateRequest,
    user=Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    if (
        data.starts_at
        and data.ends_at
        and data.ends_at <= data.starts_at
    ):
        raise HTTPException(
            status_code=400,
            detail="End time must be after start time.",
        )

    programme = (
        db.query(Programme)
        .filter(
            Programme.active.is_(True)
        )
        .order_by(Programme.id.asc())
        .first()
    )

    if not programme:
        raise HTTPException(
            status_code=404,
            detail="No active programme configured.",
        )

    values = validate_prizes(
        data.prize_values
    )

    game = RewardGame(
        programme_id=programme.id,
        name=data.name.strip(),
        description=(
            data.description.strip()
            if data.description
            else None
        ),
        game_type=data.game_type,
        prize_values=values,
        starts_at=data.starts_at,
        ends_at=data.ends_at,
        active=data.active,
        show_upcoming=data.show_upcoming,
        created_by_user_id=user.id,
    )

    db.add(game)
    db.flush()

    # Audit using the application's existing audit model.
    from ..db.models import AuditLog

    db.add(
        AuditLog(
            user_id=user.id,
            action="reward_game.created",
            entity_type="reward_game",
            entity_id=game.id,
            details=(
                f"type={game.game_type.value};"
                f"name={game.name};"
                f"prizes={values}"
            ),
        )
    )

    db.commit()

    return serialize_game(game)


@router.post("/admin/{game_id}/grant")
def grant_reward_game(
    game_id: int,
    data: GrantRewardGameRequest,
    user=Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    game = (
        db.query(RewardGame)
        .filter(
            RewardGame.id == game_id,
            RewardGame.active.is_(True),
        )
        .first()
    )

    if not game:
        raise HTTPException(
            status_code=404,
            detail="Reward game not found.",
        )

    player = (
        db.query(Player)
        .filter(
            Player.id == data.player_id,
            Player.active.is_(True),
        )
        .first()
    )

    if not player:
        raise HTTPException(
            status_code=404,
            detail="Player not found.",
        )

    if player.programme_id != game.programme_id:
        raise HTTPException(
            status_code=400,
            detail="Player does not belong to this programme.",
        )

    entitlement = PlayerRewardGame(
        game_id=game.id,
        player_id=player.id,
        status=RewardGamePlayStatus.AVAILABLE,
        granted_by_user_id=user.id,
    )

    db.add(entitlement)
    db.flush()

    from ..db.models import AuditLog

    db.add(
        AuditLog(
            user_id=user.id,
            action="reward_game.granted",
            entity_type="player_reward_game",
            entity_id=entitlement.id,
            details=(
                f"game_id={game.id};"
                f"player_id={player.id};"
                f"game_type={game.game_type.value}"
            ),
        )
    )

    db.commit()

    return {
        "success": True,
        "play_id": entitlement.id,
    }
