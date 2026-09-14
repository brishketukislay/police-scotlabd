from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models.core import Player, XPTransaction
from app.db.models.xp_balance import PlayerXPBalance, GroupXPBalance
from app.services.xp import (
    DuplicateXPTransactionError,
    GroupNotFoundError,
    InvalidXPAmountError,
    PlayerNotFoundError,
    XPError,
    award_xp,
    get_player_balance,
    programme_xp,
)


router = APIRouter(
    prefix="/api/xp",
    tags=["XP"],
)


# ============================================================
# REQUEST / RESPONSE MODELS
# ============================================================

class XPAwardRequest(BaseModel):
    programme_id: int | None = None
    player_id: int = Field(..., gt=0)

    amount: int = Field(
        ...,
        ge=-50_000,
        le=50_000,
    )

    group_amount: int = Field(
        0,
        ge=-50_000,
        le=50_000,
    )

    transaction_type: str = Field(
        ...,
        min_length=1,
        max_length=100,
    )

    reason: str = Field(
        ...,
        min_length=1,
        max_length=500,
    )

    reference_type: str | None = Field(
        None,
        max_length=100,
    )

    reference_id: int | None = None

    idempotency_key: str | None = Field(
        None,
        max_length=255,
    )

    created_by: int | None = None


# ============================================================
# HELPERS
# ============================================================

def get_active_programme_id(
    db: Session,
) -> int:
    """
    Resolve the active programme.

    Kept local to the XP API so callers do not need to know
    how the project's active programme is selected.
    """

    from app.db.models.core import Programme

    programme = (
        db.query(Programme)
        .filter(
            Programme.active == True,
        )
        .first()
    )

    if programme is None:
        raise HTTPException(
            status_code=404,
            detail="No active programme configured.",
        )

    return programme.id


def transaction_response(
    transaction: XPTransaction,
) -> dict:
    return {
        "id": transaction.id,
        "programme_id": transaction.programme_id,
        "player_id": transaction.player_id,
        "group_id": transaction.group_id,
        "amount": transaction.amount,
        "group_amount": transaction.group_amount,
        "transaction_type": transaction.transaction_type,
        "idempotency_key": transaction.idempotency_key,
        "reason": transaction.reason,
        "reference_type": transaction.reference_type,
        "reference_id": transaction.reference_id,
        "created_by": transaction.created_by,
        "created_at": transaction.created_at,
    }


# ============================================================
# AWARD XP
# ============================================================

@router.post("/awards")
def create_xp_award(
    payload: XPAwardRequest,
    db: Session = Depends(get_db),
):
    """
    Create an XP ledger transaction through the existing
    XP domain service.

    This endpoint deliberately contains no XP business logic.
    """

    if payload.amount == 0:
        raise HTTPException(
            status_code=400,
            detail="amount cannot be zero.",
        )

    player = (
        db.query(Player)
        .filter(
            Player.id == payload.player_id,
            Player.active == True,
        )
        .first()
    )

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found.",
        )

    programme_id = (
        payload.programme_id
        if payload.programme_id is not None
        else get_active_programme_id(db)
    )

    # Ensure the player belongs to the requested programme.
    if (
        getattr(player, "programme_id", programme_id)
        != programme_id
        and getattr(player, "programme_id", None) is not None
    ):
        raise HTTPException(
            status_code=400,
            detail="Player does not belong to the requested programme.",
        )

    try:
        transaction = award_xp(
            db,
            programme_id=programme_id,
            player_id=player.id,
            amount=payload.amount,
            group_amount=payload.group_amount,
            transaction_type=payload.transaction_type,
            reason=payload.reason,
            reference_type=payload.reference_type,
            reference_id=payload.reference_id,
            idempotency_key=payload.idempotency_key,
            created_by=payload.created_by,
        )

        db.commit()
        db.refresh(transaction)

    except PlayerNotFoundError as exc:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except GroupNotFoundError as exc:
        db.rollback()
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except InvalidXPAmountError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except DuplicateXPTransactionError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    except XPError as exc:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception:
        db.rollback()
        raise

    return {
        "success": True,
        "transaction": transaction_response(
            transaction,
        ),
    }


# ============================================================
# PLAYER BALANCE
# ============================================================

@router.get("/players/{player_id}/balance")
def get_xp_balance(
    player_id: int,
    db: Session = Depends(get_db),
):
    player = (
        db.query(Player)
        .filter(
            Player.id == player_id,
            Player.active == True,
        )
        .first()
    )

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found.",
        )

    balance = get_player_balance(
        db,
        player_id,
    )

    return {
        "player_id": balance.player_id,
        "current_xp": balance.current_xp,
        "lifetime_xp": balance.lifetime_xp,
    }


# ============================================================
# PROGRAMME BALANCE
# ============================================================

@router.get("/programmes/{programme_id}/balance")
def get_programme_xp_balance(
    programme_id: int,
    db: Session = Depends(get_db),
):
    balance = (
        db.query(GroupXPBalance)
        .filter(
            GroupXPBalance.programme_id == programme_id,
        )
        .first()
    )

    if balance is None:
        return {
            "programme_id": programme_id,
            "current_xp": 0,
            "lifetime_xp_awarded": 0,
            "lifetime_xp_removed": 0,
        }

    return {
        "programme_id": balance.programme_id,
        "current_xp": balance.current_xp,
        "lifetime_xp_awarded": balance.lifetime_xp_awarded,
        "lifetime_xp_removed": balance.lifetime_xp_removed,
        "updated_at": balance.updated_at,
    }


# ============================================================
# PLAYER TRANSACTION HISTORY
# ============================================================

@router.get("/players/{player_id}/transactions")
def get_player_transactions(
    player_id: int,
    limit: int = Query(
        50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        0,
        ge=0,
    ),
    db: Session = Depends(get_db),
):
    player = (
        db.query(Player)
        .filter(
            Player.id == player_id,
            Player.active == True,
        )
        .first()
    )

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found.",
        )

    query = (
        db.query(XPTransaction)
        .filter(
            XPTransaction.player_id == player_id,
        )
        .order_by(
            XPTransaction.created_at.desc(),
            XPTransaction.id.desc(),
        )
    )

    total = query.count()

    transactions = (
        query
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "player_id": player_id,
        "total": total,
        "limit": limit,
        "offset": offset,
        "items": [
            transaction_response(transaction)
            for transaction in transactions
        ],
    }


# ============================================================
# PROGRAMME XP
# ============================================================

@router.get("/programme")
def get_programme_xp(
    programme_id: int | None = None,
    db: Session = Depends(get_db),
):
    resolved_programme_id = (
        programme_id
        if programme_id is not None
        else get_active_programme_id(db)
    )

    xp = programme_xp(
        db,
        resolved_programme_id,
    )

    return {
        "programme_id": resolved_programme_id,
        "xp": xp,
    }
