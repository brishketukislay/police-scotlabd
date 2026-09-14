from __future__ import annotations

from datetime import datetime

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import func
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from ..db.models import (
    Player,
    YouthGroup,
    XPTransaction,
)
from ..db.models.xp_balance import (
    PlayerXPBalance,
    GroupXPBalance,
)

from .rewards import grant_eligible_rewards


class XPError(Exception):
    """Base XP-domain exception."""


class InvalidXPAmountError(XPError):
    pass


class DuplicateXPTransactionError(XPError):
    pass


class PlayerNotFoundError(XPError):
    pass


class GroupNotFoundError(XPError):
    pass


@dataclass(frozen=True)
class XPBalance:
    player_id: int
    lifetime_xp: int
    current_xp: int


@dataclass(frozen=True)
class XPChange:
    player_id: int
    individual_amount: int
    group_amount: int
    transaction_id: int | None
    reference: str | None


def _validate_amount(
    amount: int,
    *,
    field_name: str,
) -> int:
    """
    XP is represented as an integer.

    Negative XP is permitted because penalties are supported.

    Zero-value transactions are rejected.
    """

    if isinstance(amount, bool):
        raise InvalidXPAmountError(
            f"{field_name} must be an integer."
        )

    try:
        value = int(amount)
    except (TypeError, ValueError) as exc:
        raise InvalidXPAmountError(
            f"{field_name} must be an integer."
        ) from exc

    if value == 0:
        raise InvalidXPAmountError(
            f"{field_name} cannot be zero."
        )

    return value


def _get_player(
    db: Session,
    player_id: int,
) -> Player:
    player = db.get(Player, player_id)

    if player is None:
        raise PlayerNotFoundError(
            f"Player {player_id} was not found."
        )

    return player


def _get_group(
    db: Session,
    group_id: int,
) -> YouthGroup:
    group = db.get(YouthGroup, group_id)

    if group is None:
        raise GroupNotFoundError(
            f"Group {group_id} was not found."
        )

    return group


def _make_reference(
    reference_type: str | None,
    reference_id: int | None,
) -> str | None:
    """
    Convert database reference fields into the legacy reference string.
    """

    if reference_type is None or reference_id is None:
        return None

    return f"{reference_type}:{reference_id}"


def _parse_reference(
    reference: str | None,
) -> tuple[str | None, int | None]:
    """
    Convert legacy references such as:

        attendance:1
        challenge:7

    into:

        reference_type
        reference_id
    """

    if not reference or ":" not in reference:
        return None, None

    reference_type, reference_id_text = reference.split(":", 1)

    if not reference_type or not reference_id_text:
        return None, None

    try:
        reference_id = int(reference_id_text)
    except ValueError:
        return None, None

    return reference_type, reference_id


def _find_reference(
    db: Session,
    reference: str,
) -> XPTransaction | None:
    """
    Find an existing transaction using the legacy reference string.

    The actual XPTransaction ORM does NOT have a `reference` column.

    References are stored using:

        reference_type
        reference_id
    """

    reference_type, reference_id = _parse_reference(reference)

    if reference_type is None or reference_id is None:
        return None

    return (
        db.query(XPTransaction)
        .filter(
            XPTransaction.reference_type == reference_type,
            XPTransaction.reference_id == reference_id,
        )
        .first()
    )


def player_xp(
    db: Session,
    player_id: int,
) -> int:
    """
    Return the player's current materialised XP balance.

    The XP transaction ledger remains the source of truth, while the
    materialised balance provides the fast read path.
    """

    balance = (
        db.query(PlayerXPBalance)
        .filter(
            PlayerXPBalance.player_id == player_id,
        )
        .first()
    )

    if balance is None:
        return 0

    return int(balance.current_xp or 0)


def player_current_xp(
    db: Session,
    player_id: int,
) -> int:
    """
    Return the player's current materialised XP balance.
    """

    return player_xp(
        db,
        player_id,
    )


def get_player_balance(
    db: Session,
    player_id: int,
) -> XPBalance:
    lifetime = player_xp(
        db,
        player_id,
    )

    current = player_current_xp(
        db,
        player_id,
    )

    return XPBalance(
        player_id=player_id,
        lifetime_xp=lifetime,
        current_xp=current,
    )


def group_xp(
    db: Session,
    group_id: int | None = None,
    programme_id: int | None = None,
) -> int:
    """
    Calculate collective XP from the transaction ledger.

    Historical group XP remains attached to the group stored on the
    transaction.

    If group_id is supplied, it takes precedence over programme_id.
    """

    if programme_id is not None and group_id is None:
        balance = (
            db.query(GroupXPBalance)
            .filter(
                GroupXPBalance.programme_id == programme_id,
            )
            .first()
        )

        if balance is None:
            return 0

        return int(balance.current_xp or 0)

    if group_id is not None:
        result = (
            db.query(
                func.coalesce(
                    func.sum(XPTransaction.group_amount),
                    0,
                )
            )
            .filter(
                XPTransaction.group_id == group_id,
            )
            .scalar()
        )

        return int(result or 0)

    result = (
        db.query(
            func.coalesce(
                func.sum(XPTransaction.group_amount),
                0,
            )
        )
        .scalar()
    )

    return int(result or 0)


def programme_xp(
    db: Session,
    programme_id: int,
) -> int:
    """
    Collective XP across all groups in a programme.
    """

    return group_xp(
        db,
        programme_id=programme_id,
    )


def get_transaction_by_reference(
    db: Session,
    reference: str,
) -> XPTransaction | None:
    return _find_reference(
        db,
        reference,
    )


def award_xp(
    db: Session,
    *,
    programme_id: int,
    player_id: int | None,
    amount: int,
    group_amount: int = 0,
    transaction_type: str,
    group_id: int | None = None,
    reason: str | None = None,
    reference_type: str | None = None,
    reference_id: int | None = None,
    idempotency_key: str | None = None,
    reference: str | None = None,
    created_by: int | None = None,
) -> XPTransaction:
    """
    Create one XP ledger transaction.

    This function does not commit.

    The caller owns the database transaction.

    The actual XPTransaction ORM stores references using:

        reference_type
        reference_id

    A legacy reference such as:

        reference="attendance:1"

    is automatically converted to:

        reference_type="attendance"
        reference_id=1
    """

    # Normal XP transactions must have a non-zero individual amount.
    #
    # The exception is a group-only transaction:
    #
    #     player_id=None
    #     amount=0
    #     group_amount != 0
    #
    # Exceptional group penalties use this form so that no individual
    # player's XP is changed.

    if amount == 0:
        if player_id is not None or group_amount == 0:
            raise InvalidXPAmountError(
                "amount cannot be zero unless this is a "
                "group-only transaction."
            )
    else:
        amount = _validate_amount(
            amount,
            field_name="amount",
        )

    if group_amount != 0:
        group_amount = _validate_amount(
            group_amount,
            field_name="group_amount",
        )
    else:
        group_amount = 0

    if not transaction_type:
        raise XPError(
            "transaction_type is required."
        )

    if not reason:
        raise XPError(
            "reason is required."
        )

    player = None

    if player_id is not None:
        player = _get_player(
            db,
            player_id,
        )

        if group_id is None:
            group_id = player.group_id

    elif group_id is None:
        raise XPError(
            "Either player_id or group_id is required."
        )

    if player_id is None and amount != 0:
        raise XPError(
            "A group-only XP transaction cannot change individual XP."
        )

    # ---------------------------------------------------------------
    # Validate group target when supplied.
    # ---------------------------------------------------------------

    if group_id is not None:
        group = (
            db.query(YouthGroup)
            .filter(
                YouthGroup.id == group_id,
                YouthGroup.programme_id == programme_id,
            )
            .first()
        )

        if group is None:
            raise GroupNotFoundError(
                "Group not found in this programme."
            )

    # ---------------------------------------------------------------
    # Backwards-compatible reference parsing.
    # ---------------------------------------------------------------

    if reference and (
        reference_type is None
        or reference_id is None
    ):
        parsed_type, parsed_id = _parse_reference(
            reference
        )

        if (
            parsed_type is not None
            and parsed_id is not None
        ):
            reference_type = parsed_type
            reference_id = parsed_id

    # ---------------------------------------------------------------
    # Idempotency key.
    #
    # A supplied idempotency key represents the same logical request.
    # Repeating the same key with the same payload returns the original
    # transaction. Reusing it with different values is an error.
    # ---------------------------------------------------------------

    if idempotency_key is not None:
        idempotency_key = idempotency_key.strip()

        if not idempotency_key:
            idempotency_key = None

    if idempotency_key is not None:
        existing = (
            db.query(XPTransaction)
            .filter(
                XPTransaction.idempotency_key == idempotency_key,
            )
            .first()
        )

        if existing is not None:
            if (
                existing.programme_id != programme_id
                or existing.player_id != player_id
                or existing.group_id != group_id
                or existing.amount != amount
                or existing.group_amount != group_amount
                or existing.transaction_type != transaction_type
            ):
                raise DuplicateXPTransactionError(
                    "An XP transaction already exists for this "
                    "idempotency key with different values."
                )

            return existing

    # ---------------------------------------------------------------
    # Business-event/reference idempotency.
    # ---------------------------------------------------------------

    if (
        reference_type is not None
        and reference_id is not None
    ):
        existing = (
            db.query(XPTransaction)
            .filter(
                XPTransaction.reference_type == reference_type,
                XPTransaction.reference_id == reference_id,
            )
            .first()
        )

        if existing is not None:
            if (
                existing.player_id != player_id
                or existing.group_id != group_id
                or existing.amount != amount
                or existing.group_amount != group_amount
            ):
                raise DuplicateXPTransactionError(
                    "An XP transaction already exists "
                    "for this reference with different values."
                )

            return existing

    # ---------------------------------------------------------------
    # Create transaction.
    # ---------------------------------------------------------------

    transaction = XPTransaction(
        programme_id=programme_id,
        player_id=player_id,
        group_id=group_id,
        amount=amount,
        group_amount=group_amount,
        transaction_type=transaction_type,
        idempotency_key=idempotency_key,
        reason=reason,
        reference_type=reference_type,
        reference_id=reference_id,
        created_by=created_by,
    )

    # ---------------------------------------------------------------
    # Create transaction inside a savepoint.
    #
    # This allows a uniqueness race to be handled without rolling
    # back the caller's entire database transaction.
    # ---------------------------------------------------------------

    savepoint = db.begin_nested()

    try:
        db.add(transaction)
        db.flush()
        savepoint.commit()

    except IntegrityError as exc:
        savepoint.rollback()

        existing = None

        if idempotency_key is not None:
            existing = (
                db.query(XPTransaction)
                .filter(
                    XPTransaction.idempotency_key == idempotency_key,
                )
                .first()
            )

        if (
            existing is None
            and reference_type is not None
            and reference_id is not None
        ):
            existing = (
                db.query(XPTransaction)
                .filter(
                    XPTransaction.reference_type == reference_type,
                    XPTransaction.reference_id == reference_id,
                )
                .first()
            )

        if existing is not None:
            if (
                existing.player_id != player_id
                or existing.group_id != group_id
                or existing.amount != amount
                or existing.group_amount != group_amount
            ):
                raise DuplicateXPTransactionError(
                    "An XP transaction already exists with "
                    "different values."
                ) from exc

            return existing

        raise

    # ---------------------------------------------------------------
    # Materialised XP projections.
    #
    # The projection happens in the caller's transaction.
    # No commit occurs here.
    #
    # If either projection fails, the caller can roll back the entire
    # operation, keeping the ledger and balances consistent.
    # ---------------------------------------------------------------

    apply_xp_transaction(
        db,
        transaction,
    )

    return transaction


def award_positive_xp(
    db: Session,
    *,
    programme_id: int,
    player_id: int,
    amount: int,
    group_amount: int = 0,
    transaction_type: str,
    reason: str,
    reference: str | None = None,
    reference_type: str | None = None,
    reference_id: int | None = None,
    idempotency_key: str | None = None,
    created_by: int | None = None,
) -> XPTransaction:
    """
    Award positive XP.
    """

    amount = abs(
        _validate_amount(
            amount,
            field_name="amount",
        )
    )

    if group_amount:
        group_amount = abs(
            _validate_amount(
                group_amount,
                field_name="group_amount",
            )
        )

    return award_xp(
        db,
        programme_id=programme_id,
        player_id=player_id,
        amount=amount,
        group_amount=group_amount,
        transaction_type=transaction_type,
        reason=reason,
        reference=reference,
        reference_type=reference_type,
        reference_id=reference_id,
        idempotency_key=idempotency_key,
        created_by=created_by,
    )


def award_individual_xp(
    db: Session,
    *,
    programme_id: int,
    player_id: int,
    amount: int,
    transaction_type: str,
    reason: str,
    reference: str | None = None,
    reference_type: str | None = None,
    reference_id: int | None = None,
    idempotency_key: str | None = None,
    created_by: int | None = None,
) -> XPTransaction:
    """
    Award XP to the player without adding group XP.
    """

    return award_positive_xp(
        db,
        programme_id=programme_id,
        player_id=player_id,
        amount=amount,
        group_amount=0,
        transaction_type=transaction_type,
        reason=reason,
        reference=reference,
        reference_type=reference_type,
        reference_id=reference_id,
        idempotency_key=idempotency_key,
        created_by=created_by,
    )


def award_group_xp(
    db: Session,
    *,
    programme_id: int,
    player_id: int,
    amount: int,
    transaction_type: str,
    reason: str,
    reference: str | None = None,
    reference_type: str | None = None,
    reference_id: int | None = None,
    idempotency_key: str | None = None,
    created_by: int | None = None,
) -> XPTransaction:
    """
    Award the same XP amount to the individual and their group.
    """

    amount = abs(
        _validate_amount(
            amount,
            field_name="amount",
        )
    )

    return award_xp(
        db,
        programme_id=programme_id,
        player_id=player_id,
        amount=amount,
        group_amount=amount,
        transaction_type=transaction_type,
        reason=reason,
        reference=reference,
        reference_type=reference_type,
        reference_id=reference_id,
        idempotency_key=idempotency_key,
        created_by=created_by,
    )


def award_negative_xp(
    db: Session,
    *,
    programme_id: int,
    player_id: int,
    amount: int,
    group_amount: int = 0,
    transaction_type: str = "penalty",
    reason: str,
    reference: str | None = None,
    reference_type: str | None = None,
    reference_id: int | None = None,
    idempotency_key: str | None = None,
    created_by: int | None = None,
) -> XPTransaction:
    """
    Deduct XP through a negative ledger transaction.

    The supplied amount may be positive or negative.
    The stored player amount is always negative.
    """

    amount = abs(
        _validate_amount(
            amount,
            field_name="amount",
        )
    )

    if group_amount:
        group_amount = -abs(
            _validate_amount(
                group_amount,
                field_name="group_amount",
            )
        )

    return award_xp(
        db,
        programme_id=programme_id,
        player_id=player_id,
        amount=-amount,
        group_amount=group_amount,
        transaction_type=transaction_type,
        reason=reason,
        reference=reference,
        reference_type=reference_type,
        reference_id=reference_id,
        idempotency_key=idempotency_key,
        created_by=created_by,
    )


def award_penalty_xp(
    db: Session,
    *,
    programme_id: int,
    player_id: int,
    amount: int,
    group_amount: int = 0,
    transaction_type: str = "penalty",
    reason: str,
    reference: str | None = None,
    reference_type: str | None = None,
    reference_id: int | None = None,
    created_by: int | None = None,
) -> XPTransaction:
    """
    Backwards-compatible alias for award_negative_xp.
    """

    return award_negative_xp(
        db,
        programme_id=programme_id,
        player_id=player_id,
        amount=amount,
        group_amount=group_amount,
        transaction_type=transaction_type,
        reason=reason,
        reference=reference,
        reference_type=reference_type,
        reference_id=reference_id,
        created_by=created_by,
    )


def award_group_penalty_xp(
    db: Session,
    *,
    programme_id: int,
    player_id: int,
    amount: int,
    transaction_type: str = "group_penalty",
    reason: str,
    reference: str | None = None,
    reference_type: str | None = None,
    reference_id: int | None = None,
    created_by: int | None = None,
) -> XPTransaction:
    """
    Deduct the supplied XP from both the player and their group.
    """

    amount = abs(
        _validate_amount(
            amount,
            field_name="amount",
        )
    )

    return award_negative_xp(
        db,
        programme_id=programme_id,
        player_id=player_id,
        amount=amount,
        group_amount=amount,
        transaction_type=transaction_type,
        reason=reason,
        reference=reference,
        reference_type=reference_type,
        reference_id=reference_id,
        created_by=created_by,
    )


def transactions_for_player(
    db: Session,
    player_id: int,
) -> list[XPTransaction]:
    """
    Return a player's XP transactions newest first.
    """

    return (
        db.query(XPTransaction)
        .filter(
            XPTransaction.player_id == player_id,
        )
        .order_by(
            XPTransaction.created_at.desc(),
            XPTransaction.id.desc(),
        )
        .all()
    )


def transactions_for_group(
    db: Session,
    group_id: int,
) -> list[XPTransaction]:
    """
    Return a group's XP transactions newest first.
    """

    return (
        db.query(XPTransaction)
        .filter(
            XPTransaction.group_id == group_id,
        )
        .order_by(
            XPTransaction.created_at.desc(),
            XPTransaction.id.desc(),
        )
        .all()
    )


def balance_from_transactions(
    transactions: Iterable[XPTransaction],
) -> int:
    """
    Calculate net individual XP from a collection of transactions.
    """

    return sum(
        int(transaction.amount or 0)
        for transaction in transactions
    )


def transaction_to_dict(
    transaction: XPTransaction,
) -> dict:
    """
    Convert an XP transaction to a JSON-friendly dictionary.
    """

    return {
        "id": transaction.id,
        "programme_id": transaction.programme_id,
        "player_id": transaction.player_id,
        "group_id": transaction.group_id,
        "amount": transaction.amount,
        "group_amount": transaction.group_amount,
        "transaction_type": transaction.transaction_type,
        "reason": transaction.reason,
        "reference_type": transaction.reference_type,
        "reference_id": transaction.reference_id,
        "reference": _make_reference(
            transaction.reference_type,
            transaction.reference_id,
        ),
        "created_by": transaction.created_by,
        "created_at": transaction.created_at,
    }


# ============================================================

# ============================================================

def apply_player_xp(
    db: Session,
    *,
    player_id: int,
    amount: int,
) -> "PlayerXPBalance":
    """
    Apply an XP ledger change to the player's materialised balance.

    The XP transaction ledger remains the source of truth.

    Positive amounts:
        current_xp += amount
        lifetime_xp += amount

    Negative amounts:
        current_xp += amount
        lifetime_xp_removed += abs(amount)

    This function does not commit.
    """

    from ..db.models.xp_balance import PlayerXPBalance

    balance = (
        db.query(PlayerXPBalance)
        .filter(
            PlayerXPBalance.player_id == player_id,
        )
        .with_for_update()
        .first()
    )

    if balance is None:
        balance = PlayerXPBalance(
            player_id=player_id,
            current_xp=0,
            lifetime_xp=0,
            lifetime_xp_removed=0,
        )

        db.add(balance)
        db.flush()

    balance.current_xp += amount

    if amount > 0:
        balance.lifetime_xp += amount
    elif amount < 0:
        balance.lifetime_xp_removed += abs(amount)

    balance.updated_at = datetime.utcnow()

    db.flush()

    return balance


def apply_group_xp(
    db: Session,
    *,
    programme_id: int,
    amount: int,
) -> "GroupXPBalance":
    """
    Apply a collective XP change to the programme-wide group balance.

    Positive amounts increase the collective balance and lifetime awarded.

    Negative amounts reduce the current balance and increase lifetime
    removed.

    This function does not commit.
    """

    from ..db.models.xp_balance import GroupXPBalance

    balance = (
        db.query(GroupXPBalance)
        .filter(
            GroupXPBalance.programme_id == programme_id,
        )
        .with_for_update()
        .first()
    )

    if balance is None:
        balance = GroupXPBalance(
            programme_id=programme_id,
            current_xp=0,
            lifetime_xp_awarded=0,
            lifetime_xp_removed=0,
        )

        db.add(balance)
        db.flush()

    balance.current_xp += amount

    if amount > 0:
        balance.lifetime_xp_awarded += amount
    elif amount < 0:
        balance.lifetime_xp_removed += abs(amount)

    balance.updated_at = datetime.utcnow()

    db.flush()

    return balance


def _advance_active_skill_tree(
    db: Session,
    *,
    player_id: int,
    amount: int,
) -> None:
    """
    Apply a player's XP transaction to their active skill tree.

    Skill-tree XP is intentionally separate from lifetime/player XP.
    Creating a new skill tree starts its progress from zero.

    Negative XP can reduce current skill-tree progress, but never
    marks a previously completed milestone as incomplete.
    """

    if amount == 0:
        return

    from ..db.models import SkillTree

    tree = (
        db.query(SkillTree)
        .filter(
            SkillTree.player_id == player_id,
            SkillTree.active == True,
            SkillTree.completed == False,
        )
        .order_by(
            SkillTree.id.desc(),
        )
        .first()
    )

    if tree is None:
        return

    tree.current_xp = max(
        0,
        int(tree.current_xp or 0) + amount,
    )

    for milestone in sorted(
        tree.milestones,
        key=lambda item: (
            item.required_xp,
            item.id,
        ),
    ):
        if (
            not milestone.completed
            and tree.current_xp >= milestone.required_xp
        ):
            milestone.completed = True
            milestone.completed_at = datetime.utcnow()

    if (
        tree.milestones
        and all(
            milestone.completed
            for milestone in tree.milestones
        )
    ):
        tree.completed = True
        tree.active = False
        tree.completed_at = datetime.utcnow()

    db.flush()


def apply_xp_transaction(
    db: Session,
    transaction: XPTransaction,
) -> tuple["PlayerXPBalance | None", "GroupXPBalance | None"]:
    """
    Apply one persisted XP transaction to all materialised balances.

    The caller owns the transaction boundary.

    No commit is performed here.

    A transaction may affect:

        1. player balance, when player_id is present
        2. programme-wide collective balance, when group_amount is non-zero

    This supports both player XP transactions and collective
    programme/group transactions.

    The collective balance uses XPTransaction.group_amount rather than
    XPTransaction.amount.
    """

    player_balance = None

    if (
        transaction.player_id is not None
        and transaction.amount != 0
    ):
        player_balance = apply_player_xp(
            db,
            player_id=transaction.player_id,
            amount=transaction.amount,
        )

        _advance_active_skill_tree(
            db,
            player_id=transaction.player_id,
            amount=transaction.amount,
        )

    group_balance = None

    if (
        transaction.programme_id is not None
        and transaction.group_amount != 0
    ):
        group_balance = apply_group_xp(
            db,
            programme_id=transaction.programme_id,
            amount=transaction.group_amount,
        )

    return (
        player_balance,
        group_balance,
    )
