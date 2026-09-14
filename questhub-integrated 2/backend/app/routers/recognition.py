from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.database import get_db


router = APIRouter(
    prefix="/api/recognition",
    tags=["recognition"],
)


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def hash_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()


# ------------------------------------------------------------------
# SCHEMAS
# ------------------------------------------------------------------

class RecognitionTokenResponse(BaseModel):
    token: str
    player_id: int
    gamertag: str


class RecognitionPlayerResponse(BaseModel):
    player_id: int
    gamertag: str
    avatar: str | None = None


class RecognitionSubmission(BaseModel):
    token: str = Field(
        min_length=16,
        max_length=256,
    )

    category: str = Field(
        min_length=1,
        max_length=100,
    )

    description: str = Field(
        min_length=3,
        max_length=1000,
    )

    submitted_by_name: str = Field(
        min_length=1,
        max_length=200,
    )

    submitted_by_contact: str = Field(
        min_length=1,
        max_length=300,
    )


# ------------------------------------------------------------------
# CREATE PLAYER QR TOKEN
# ------------------------------------------------------------------

@router.post(
    "/token",
    response_model=RecognitionTokenResponse,
)
def create_recognition_token(
    player_id: int,
    db: Session = Depends(get_db),
):
    player = db.execute(
        text(
            """
            SELECT
                id,
                gamertag
            FROM players
            WHERE id = :player_id
            LIMIT 1
            """
        ),
        {
            "player_id": player_id,
        },
    ).mappings().first()

    if not player:
        raise HTTPException(
            status_code=404,
            detail="Player not found.",
        )

    raw_token = secrets.token_urlsafe(32)
    token_hash = hash_token(raw_token)
    now = utc_now()

    try:
        # Deactivate previous codes for this player.
        db.execute(
            text(
                """
                UPDATE recognition_tokens
                SET active = 0
                WHERE player_id = :player_id
                """
            ),
            {
                "player_id": player_id,
            },
        )

        # Store only the hash, never the raw token.
        db.execute(
            text(
                """
                INSERT INTO recognition_tokens (
                    player_id,
                    token_hash,
                    created_at,
                    active
                )
                VALUES (
                    :player_id,
                    :token_hash,
                    :created_at,
                    1
                )
                """
            ),
            {
                "player_id": player["id"],
                "token_hash": token_hash,
                "created_at": now,
            },
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "token": raw_token,
        "player_id": player["id"],
        "gamertag": player["gamertag"],
    }


# ------------------------------------------------------------------
# LOOK UP PLAYER FROM QR TOKEN
# ------------------------------------------------------------------

@router.get(
    "/lookup",
    response_model=RecognitionPlayerResponse,
)
def lookup_recognition_token(
    token: str,
    db: Session = Depends(get_db),
):
    token = token.strip()

    if not token:
        raise HTTPException(
            status_code=400,
            detail="Recognition token is required.",
        )

    token_hash = hash_token(token)

    player = db.execute(
        text(
            """
            SELECT
                p.id AS player_id,
                p.gamertag,
                p.avatar
            FROM recognition_tokens rt
            INNER JOIN players p
                ON p.id = rt.player_id
            WHERE rt.token_hash = :token_hash
              AND rt.active = 1
            LIMIT 1
            """
        ),
        {
            "token_hash": token_hash,
        },
    ).mappings().first()

    if not player:
        raise HTTPException(
            status_code=404,
            detail="Recognition code is invalid or expired.",
        )

    return dict(player)


# ------------------------------------------------------------------
# SUBMIT COMMUNITY RECOGNITION
# ------------------------------------------------------------------

@router.post(
    "/submit",
)
def submit_recognition(
    payload: RecognitionSubmission,
    db: Session = Depends(get_db),
):
    token = payload.token.strip()

    if not token:
        raise HTTPException(
            status_code=400,
            detail="Recognition token is required.",
        )

    token_hash = hash_token(token)

    player = db.execute(
        text(
            """
            SELECT
                p.id,
                p.gamertag
            FROM recognition_tokens rt
            INNER JOIN players p
                ON p.id = rt.player_id
            WHERE rt.token_hash = :token_hash
              AND rt.active = 1
            LIMIT 1
            """
        ),
        {
            "token_hash": token_hash,
        },
    ).mappings().first()

    if not player:
        raise HTTPException(
            status_code=404,
            detail="Recognition code is invalid or expired.",
        )

    # Determine the active programme.
    programme = db.execute(
        text(
            """
            SELECT id
            FROM programmes
            ORDER BY id
            LIMIT 1
            """
        )
    ).mappings().first()

    if not programme:
        raise HTTPException(
            status_code=500,
            detail="No programme is configured.",
        )

    programme_id = programme["id"]

    # Community awards are reviewed by staff/admin before XP
    # is awarded. We deliberately create a pending award here.
    now = utc_now()

    try:
        result = db.execute(
            text(
                """
                INSERT INTO community_awards (
                    programme_id,
                    player_id,
                    category,
                    description,
                    submitted_by_name,
                    submitted_by_contact,
                    status,
                    xp,
                    created_at,
                    updated_at
                )
                VALUES (
                    :programme_id,
                    :player_id,
                    :category,
                    :description,
                    :submitted_by_name,
                    :submitted_by_contact,
                    'pending',
                    0,
                    :created_at,
                    :updated_at
                )
                """
            ),
            {
                "programme_id": programme_id,
                "player_id": player["id"],
                "category": payload.category.strip(),
                "description": payload.description.strip(),
                "submitted_by_name": payload.submitted_by_name.strip(),
                "submitted_by_contact": payload.submitted_by_contact.strip(),
                "created_at": now,
                "updated_at": now,
            },
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "player_id": player["id"],
        "gamertag": player["gamertag"],
        "award_id": result.lastrowid,
        "status": "pending",
    }
