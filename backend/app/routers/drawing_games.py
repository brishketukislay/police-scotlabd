from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, model_validator
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.auth import require_roles
from app.db.database import get_db
from app.db.models import (
    AuditLog,
    Player,
    YouthGroup,
)
import json

from app.services.drawing_accuracy import (
    SUPPORTED_SHAPES,
    calculate_accuracy,
    resolve_xp,
)
from app.services.xp import award_xp

router = APIRouter(
    prefix="/api/drawing-games",
    tags=["drawing-games"],
)


def ensure_tables(db: Session) -> None:
    """
    Lightweight SQLite-safe migration.

    The project currently uses SQLite for the pilot and already has a
    migration/bootstrap layer. These CREATE IF NOT EXISTS statements make
    this feature safe for an existing development database as well.
    """

    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS drawing_games (
                id INTEGER PRIMARY KEY,
                programme_id INTEGER NOT NULL,
                created_by_user_id INTEGER,
                name VARCHAR(200) NOT NULL,
                description TEXT,
                shape VARCHAR(30) NOT NULL,
                config JSON NOT NULL,
                xp_brackets JSON NOT NULL,
                active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL
            )
            """
        )
    )

    db.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS
            ix_drawing_games_programme
            ON drawing_games(programme_id)
            """
        )
    )

    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS drawing_game_assignments (
                id INTEGER PRIMARY KEY,
                game_id INTEGER NOT NULL,
                programme_id INTEGER NOT NULL,
                player_id INTEGER NOT NULL,
                assigned_by_user_id INTEGER,
                source_group_id INTEGER,
                status VARCHAR(30) NOT NULL DEFAULT 'assigned',
                assigned_at DATETIME NOT NULL,
                completed_at DATETIME,
                UNIQUE(game_id, player_id)
            )
            """
        )
    )

    db.execute(
        text(
            """
            CREATE INDEX IF NOT EXISTS
            ix_drawing_game_assignments_player
            ON drawing_game_assignments(player_id)
            """
        )
    )

    db.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS drawing_game_attempts (
                id INTEGER PRIMARY KEY,
                assignment_id INTEGER NOT NULL UNIQUE,
                player_id INTEGER NOT NULL,
                accuracy_percent FLOAT NOT NULL,
                awarded_xp INTEGER NOT NULL,
                result_metadata JSON NOT NULL,
                xp_transaction_id INTEGER,
                created_at DATETIME NOT NULL
            )
            """
        )
    )

    db.commit()


class XPBracket(BaseModel):
    min: int = Field(ge=0, le=100)
    max: int = Field(ge=0, le=100)
    xp: int = Field(ge=0, le=1_000_000)

    @model_validator(mode="after")
    def valid_range(self):
        if self.max < self.min:
            raise ValueError("Maximum percentage must be >= minimum.")
        return self


class DrawingGameConfig(BaseModel):
    timeLimit: int = Field(ge=5, le=300)  # 5 seconds to 5 minutes
    canvasWidth: int = Field(default=800, ge=100, le=2000)
    canvasHeight: int = Field(default=600, ge=100, le=2000)
    strokeWidth: int = Field(default=5, ge=1, le=50)

class CreateDrawingGameRequest(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    description: str | None = Field(
        default=None,
        max_length=2000,
    )
    shape: str
    config: DrawingGameConfig
    xp_brackets: list[XPBracket] = Field(
        min_length=1,
        max_length=20,
    )
    active: bool = Field(default=True)


class AssignDrawingGameRequest(BaseModel):
    player_ids: list[int] = Field(
        default_factory=list,
        max_length=500,
    )
    group_id: int | None = None

    @model_validator(mode="after")
    def validate_target(self):
        if not self.player_ids and self.group_id is None:
            raise ValueError(
                "Provide player_ids or group_id."
            )

        if self.player_ids and self.group_id is not None:
            raise ValueError(
                "Use either player_ids or group_id, not both."
            )

        return self


class SubmitDrawingAttemptRequest(BaseModel):
    points: list[dict[str, float]] = Field(
        min_length=8,
        max_length=2000,
    )


def active_programme_id(db: Session) -> int:
    row = db.execute(
        text(
            """
            SELECT id
            FROM programmes
            WHERE active = 1
            ORDER BY id ASC
            LIMIT 1
            """
        )
    ).first()

    if not row:
        raise HTTPException(
            status_code=404,
            detail="No active programme configured.",
        )

    return int(row[0])


def validate_brackets(
    brackets: list[XPBracket],
) -> list[dict[str, int]]:
    ordered = sorted(
        [item.model_dump() for item in brackets],
        key=lambda item: item["min"],
    )

    if ordered[0]["min"] != 0:
        raise HTTPException(
            status_code=400,
            detail="XP brackets must start at 0%.",
        )

    if ordered[-1]["max"] != 100:
        raise HTTPException(
            status_code=400,
            detail="XP brackets must end at 100%.",
        )

    for index in range(1, len(ordered)):
        previous = ordered[index - 1]
        current = ordered[index]

        if current["min"] != previous["max"] + 1:
            raise HTTPException(
                status_code=400,
                detail=(
                    "XP brackets must cover 0-100% without gaps "
                    "or overlaps."
                ),
            )

    return ordered


def game_dict(row) -> dict:
    return {
        "id": row.id,
        "name": row.name,
        "description": row.description,
        "shape": row.shape,
        "config": row.config,
        "xp_brackets": row.xp_brackets,
        "active": bool(row.active),
        "created_at": row.created_at,
    }


@router.get("/player")
def player_games(
    user=Depends(require_roles("player")),
    db: Session = Depends(get_db),
):
    ensure_tables(db)

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

    rows = db.execute(
        text(
            """
            SELECT
                a.id,
                a.game_id,
                a.status,
                g.name,
                g.description,
                g.shape,
                g.config,
                g.xp_brackets
            FROM drawing_game_assignments a
            JOIN drawing_games g ON g.id = a.game_id
            WHERE a.player_id = :player_id
              AND a.status = 'assigned'
              AND g.active = 1
            ORDER BY a.assigned_at DESC
            """
        ),
        {"player_id": player.id},
    ).mappings().all()

    return [
        {
            "assignment_id": row["id"],
            "game_id": row["game_id"],
            "name": row["name"],
            "description": row["description"],
            "shape": row["shape"],
            "config": row["config"],
        }
        for row in rows
    ]


@router.post("/admin")
def create_game(
    data: CreateDrawingGameRequest,
    user=Depends(require_roles("youth_worker", "admin")),
    db: Session = Depends(get_db),
):
    ensure_tables(db)

    if data.shape not in SUPPORTED_SHAPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported shape.",
        )

    brackets = validate_brackets(data.xp_brackets)
    programme_id = active_programme_id(db)

    now = datetime.now(timezone.utc)

    result = db.execute(
        text(
            """
            INSERT INTO drawing_games (
                programme_id,
                created_by_user_id,
                name,
                description,
                shape,
                config,
                xp_brackets,
                active,
                created_at
            )
            VALUES (
                :programme_id,
                :created_by_user_id,
                :name,
                :description,
                :shape,
                :config,
                :xp_brackets,
                :active,
                :created_at
            )
            """
        ),
        {
            "programme_id": programme_id,
            "created_by_user_id": user.id,
            "name": data.name.strip(),
            "description": (
                data.description.strip()
                if data.description
                else None
            ),
            "shape": data.shape,
            "config": json.dumps(data.config.model_dump()),
            "xp_brackets": json.dumps(brackets),
            "active": 1 if data.active else 0,  # SQLite uses 1/0 for boolean
            "created_at": now,
        },
    )

    game_id = result.lastrowid

    db.add(
        AuditLog(
            user_id=user.id,
            action="drawing_game.created",
            entity_type="drawing_game",
            entity_id=game_id,
            details=(
                f"shape={data.shape};"
                f"name={data.name};"
                f"xp_brackets={brackets}"
            ),
        )
    )

    db.commit()

    return {
        "id": game_id,
        "name": data.name.strip(),
        "shape": data.shape,
        "xp_brackets": brackets,
    }


@router.get("/admin")
def list_games(
    _=Depends(require_roles("youth_worker", "admin")),
    db: Session = Depends(get_db),
):
    ensure_tables(db)

    programme_id = active_programme_id(db)

    rows = db.execute(
        text(
            """
            SELECT *
            FROM drawing_games
            WHERE programme_id = :programme_id
            ORDER BY id DESC
            """
        ),
        {"programme_id": programme_id},
    ).mappings().all()

    return [dict(row) for row in rows]


@router.put("/admin/{game_id}")
def update_game(
    game_id: int,
    data: CreateDrawingGameRequest,
    user=Depends(require_roles("youth_worker", "admin")),
    db: Session = Depends(get_db),
):
    ensure_tables(db)

    if data.shape not in SUPPORTED_SHAPES:
        raise HTTPException(
            status_code=400,
            detail="Unsupported shape.",
        )

    brackets = validate_brackets(data.xp_brackets)
    programme_id = active_programme_id(db)

    # Ensure the game exists and belongs to the active programme
    game = db.execute(
        text(
            """
            SELECT id
            FROM drawing_games
            WHERE id = :game_id
              AND programme_id = :programme_id
            """
        ),
        {"game_id": game_id, "programme_id": programme_id},
    ).first()

    if not game:
        raise HTTPException(
            status_code=404,
            detail="Drawing game not found.",
        )

    now = datetime.now(timezone.utc)

    db.execute(
        text(
            """
            UPDATE drawing_games
            SET
                name = :name,
                description = :description,
                shape = :shape,
                config = :config,
                xp_brackets = :xp_brackets,
                active = :active,
                created_at = :created_at,
                created_by_user_id = :created_by_user_id
            WHERE id = :game_id
            """
        ),
        {
            "game_id": game_id,
            "name": data.name.strip(),
            "description": (data.description.strip() if data.description else None),
            "shape": data.shape,
            "config": json.dumps(data.config.model_dump()),
            "xp_brackets": json.dumps(brackets),
            "active": 1 if data.active else 0,  # SQLite uses 1/0 for boolean
            "created_at": now,
            "created_by_user_id": user.id,
        },
    )

    db.add(
        AuditLog(
            user_id=user.id,
            action="drawing_game.updated",
            entity_type="drawing_game",
            entity_id=game_id,
            details=(
                f"shape={data.shape};"
                f"name={data.name};"
                f"xp_brackets={brackets}"
            ),
        )
    )

    db.commit()

    return {
        "id": game_id,
        "name": data.name.strip(),
        "shape": data.shape,
        "xp_brackets": brackets,
    }


@router.post("/{game_id}/assign")
def assign_game(
    game_id: int,
    data: AssignDrawingGameRequest,
    user=Depends(require_roles("youth_worker", "admin")),
    db: Session = Depends(get_db),
):
    ensure_tables(db)

    programme_id = active_programme_id(db)

    game = db.execute(
        text(
            """
            SELECT id
            FROM drawing_games
            WHERE id = :game_id
              AND programme_id = :programme_id
              AND active = 1
            """
        ),
        {
            "game_id": game_id,
            "programme_id": programme_id,
        },
    ).first()

    if not game:
        raise HTTPException(
            status_code=404,
            detail="Drawing game not found.",
        )

    if data.group_id is not None:
        group = (
            db.query(YouthGroup)
            .filter(
                YouthGroup.id == data.group_id,
                YouthGroup.programme_id == programme_id,
                YouthGroup.active.is_(True),
            )
            .first()
        )

        if not group:
            raise HTTPException(
                status_code=404,
                detail="Group not found.",
            )

        players = (
            db.query(Player)
            .filter(
                Player.group_id == group.id,
                Player.programme_id == programme_id,
                Player.active.is_(True),
            )
            .all()
        )
        source_group_id = group.id
    else:
        players = (
            db.query(Player)
            .filter(
                Player.id.in_(data.player_ids),
                Player.programme_id == programme_id,
                Player.active.is_(True),
            )
            .all()
        )
        source_group_id = None

        if len(players) != len(set(data.player_ids)):
            raise HTTPException(
                status_code=400,
                detail=(
                    "One or more selected players are not "
                    "in the active programme."
                ),
            )

    created = []

    for player in players:
        existing = db.execute(
            text(
                """
                SELECT id
                FROM drawing_game_assignments
                WHERE game_id = :game_id
                  AND player_id = :player_id
                """
            ),
            {
                "game_id": game_id,
                "player_id": player.id,
            },
        ).mappings().first()

        if existing:
            # Delete existing assignment to allow re-assignment
            db.execute(
                text("DELETE FROM drawing_game_assignments WHERE id = :id"),
                {"id": existing["id"]},
            )
            # Continue to create a new assignment below

        result = db.execute(
            text(
                """
                INSERT INTO drawing_game_assignments (
                    game_id,
                    programme_id,
                    player_id,
                    assigned_by_user_id,
                    source_group_id,
                    status,
                    assigned_at
                )
                VALUES (
                    :game_id,
                    :programme_id,
                    :player_id,
                    :assigned_by_user_id,
                    :source_group_id,
                    'assigned',
                    :assigned_at
                )
                """
            ),
            {
                "game_id": game_id,
                "programme_id": programme_id,
                "player_id": player.id,
                "assigned_by_user_id": user.id,
                "source_group_id": source_group_id,
                "assigned_at": datetime.now(timezone.utc),
            },
        )

        created.append(int(result.lastrowid))

    db.add(
        AuditLog(
            user_id=user.id,
            action="drawing_game.assigned",
            entity_type="drawing_game",
            entity_id=game_id,
            details=(
                f"player_count={len(created)};"
                f"group_id={source_group_id}"
            ),
        )
    )

    db.commit()

    return {
        "success": True,
        "assignment_ids": created,
        "assigned_count": len(created),
    }


@router.get("/assignments")
def worker_assignments(
    _=Depends(require_roles("youth_worker", "admin")),
    db: Session = Depends(get_db),
):
    ensure_tables(db)

    programme_id = active_programme_id(db)

    rows = db.execute(
        text(
            """
            SELECT
                a.id,
                a.game_id,
                a.player_id,
                a.status,
                a.assigned_at,
                a.completed_at,
                p.gamertag,
                g.name AS game_name
            FROM drawing_game_assignments a
            JOIN players p ON p.id = a.player_id
            JOIN drawing_games g ON g.id = a.game_id
            WHERE a.programme_id = :programme_id
            ORDER BY a.id DESC
            """
        ),
        {"programme_id": programme_id},
    ).mappings().all()

    return [dict(row) for row in rows]


@router.post("/assignments/{assignment_id}/attempt")
def submit_attempt(
    assignment_id: int,
    data: SubmitDrawingAttemptRequest,
    user=Depends(require_roles("player")),
    db: Session = Depends(get_db),
):
    ensure_tables(db)

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

    assignment = db.execute(
        text(
            """
            SELECT
                a.id,
                a.game_id,
                a.status,
                g.shape,
                g.xp_brackets,
                g.name
            FROM drawing_game_assignments a
            JOIN drawing_games g ON g.id = a.game_id
            WHERE a.id = :assignment_id
              AND a.player_id = :player_id
              AND g.active = 1
            """
        ),
        {
            "assignment_id": assignment_id,
            "player_id": player.id,
        },
    ).mappings().first()

    if not assignment:
        raise HTTPException(
            status_code=404,
            detail="Game assignment not found.",
        )

    if assignment["status"] != "assigned":
        raise HTTPException(
            status_code=409,
            detail="This game has already been completed.",
        )

    existing = db.execute(
        text(
            """
            SELECT id
            FROM drawing_game_attempts
            WHERE assignment_id = :assignment_id
            """
        ),
        {"assignment_id": assignment_id},
    ).first()

    if existing:
        raise HTTPException(
            status_code=409,
            detail="This game has already been completed.",
        )

    points = []

    for point in data.points:
        x = float(point["x"])
        y = float(point["y"])

        if not (
            -0.1 <= x <= 1.1
            and -0.1 <= y <= 1.1
        ):
            raise HTTPException(
                status_code=400,
                detail="Drawing coordinates are invalid.",
            )

        points.append({"x": x, "y": y})

    accuracy = calculate_accuracy(
        assignment["shape"],
        points,
    )

    awarded_xp = resolve_xp(
        accuracy,
        json.loads(assignment["xp_brackets"]),
    )

    if awarded_xp <= 0:
        raise HTTPException(
            status_code=400,
            detail="This game configuration awards no XP.",
        )

    attempt_result = db.execute(
        text(
            """
            INSERT INTO drawing_game_attempts (
                assignment_id,
                player_id,
                accuracy_percent,
                awarded_xp,
                result_metadata,
                created_at
            )
            VALUES (
                :assignment_id,
                :player_id,
                :accuracy,
                :awarded_xp,
                :metadata,
                :created_at
            )
            """
        ),
        {
            "assignment_id": assignment_id,
            "player_id": player.id,
            "accuracy": accuracy,
            "awarded_xp": awarded_xp,
            "metadata": json.dumps({
                "shape": assignment["shape"],
                "point_count": len(points),
            }),
            "created_at": datetime.now(timezone.utc),
        },
    )

    attempt_id = int(attempt_result.lastrowid)

    transaction = award_xp(
        db,
        programme_id=player.programme_id,
        player_id=player.id,
        amount=awarded_xp,
        group_amount=0,
        transaction_type="drawing_game",
        reason=(
            f"{assignment['name']}: "
            f"{accuracy:.2f}% accuracy"
        ),
        reference_type="drawing_game_attempt",
        reference_id=attempt_id,
        idempotency_key=(
            f"drawing-game-attempt:{attempt_id}"
        ),
        created_by=user.id,
    )

    db.execute(
        text(
            """
            UPDATE drawing_game_attempts
            SET xp_transaction_id = :transaction_id
            WHERE id = :attempt_id
            """
        ),
        {
            "transaction_id": transaction.id,
            "attempt_id": attempt_id,
        },
    )

    db.execute(
        text(
            """
            UPDATE drawing_game_assignments
            SET
                status = 'completed',
                completed_at = :completed_at
            WHERE id = :assignment_id
            """
        ),
        {
            "completed_at": datetime.now(timezone.utc),
            "assignment_id": assignment_id,
        },
    )

    db.commit()

    return {
        "success": True,
        "attempt_id": attempt_id,
        "accuracy_percent": accuracy,
        "awarded_xp": awarded_xp,
    }
