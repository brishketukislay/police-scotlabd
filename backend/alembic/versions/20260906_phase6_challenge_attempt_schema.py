"""align challenge attempt workflow schema

Revision ID: 20260906_phase6_challenge_attempt_schema
Revises: 20260906_point_rule_awards_per_week
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260906_phase6_challenge_attempt_schema"
down_revision: Union[str, Sequence[str], None] = (
    "20260906_point_rule_awards_per_week"
)
branch_labels = None
depends_on = None


CHALLENGE_ATTEMPT_COLUMNS = {
    "attempt_reference": sa.Column(
        "attempt_reference",
        sa.String(length=100),
        nullable=True,
    ),
    "status": sa.Column(
        "status",
        sa.String(length=30),
        nullable=True,
    ),
    "evidence_type": sa.Column(
        "evidence_type",
        sa.String(length=50),
        nullable=True,
    ),
    "evidence_payload": sa.Column(
        "evidence_payload",
        sa.Text(),
        nullable=True,
    ),
    "rejection_reason": sa.Column(
        "rejection_reason",
        sa.Text(),
        nullable=True,
    ),
    "verified_by": sa.Column(
        "verified_by",
        sa.Integer(),
        nullable=True,
    ),
    "verified_at": sa.Column(
        "verified_at",
        sa.DateTime(),
        nullable=True,
    ),
    "percentile": sa.Column(
        "percentile",
        sa.Float(),
        nullable=True,
    ),
    "elite": sa.Column(
        "elite",
        sa.Boolean(),
        nullable=True,
    ),
    "winner": sa.Column(
        "winner",
        sa.Boolean(),
        nullable=True,
    ),
    "participation_xp": sa.Column(
        "participation_xp",
        sa.Integer(),
        nullable=True,
    ),
    "elite_xp": sa.Column(
        "elite_xp",
        sa.Integer(),
        nullable=True,
    ),
    "winner_xp": sa.Column(
        "winner_xp",
        sa.Integer(),
        nullable=True,
    ),
    "individual_xp": sa.Column(
        "individual_xp",
        sa.Integer(),
        nullable=True,
    ),
    "group_xp": sa.Column(
        "group_xp",
        sa.Integer(),
        nullable=True,
    ),
}


def _existing_columns(bind, table_name):
    inspector = sa.inspect(bind)
    return {
        column["name"]
        for column in inspector.get_columns(table_name)
    }


def _existing_indexes(bind, table_name):
    inspector = sa.inspect(bind)
    return {
        index["name"]
        for index in inspector.get_indexes(table_name)
    }


def upgrade() -> None:
    bind = op.get_bind()

    existing_columns = _existing_columns(bind, "challenge_attempts")

    # These columns were introduced in the SQLAlchemy model without a
    # corresponding migration. Add them for clean databases, while allowing
    # already-created local databases to pass through safely.
    missing = [
        column
        for name, column in CHALLENGE_ATTEMPT_COLUMNS.items()
        if name not in existing_columns
    ]

    if missing:
        with op.batch_alter_table("challenge_attempts") as batch_op:
            for column in missing:
                batch_op.add_column(column)

    # Populate safe values before making the fields NOT NULL.
    bind.execute(
        sa.text(
            """
            UPDATE challenge_attempts
            SET status = 'created'
            WHERE status IS NULL
            """
        )
    )

    bind.execute(
        sa.text(
            """
            UPDATE challenge_attempts
            SET elite = 0
            WHERE elite IS NULL
            """
        )
    )

    bind.execute(
        sa.text(
            """
            UPDATE challenge_attempts
            SET winner = 0
            WHERE winner IS NULL
            """
        )
    )

    bind.execute(
        sa.text(
            """
            UPDATE challenge_attempts
            SET participation_xp = 0
            WHERE participation_xp IS NULL
            """
        )
    )

    bind.execute(
        sa.text(
            """
            UPDATE challenge_attempts
            SET elite_xp = 0
            WHERE elite_xp IS NULL
            """
        )
    )

    bind.execute(
        sa.text(
            """
            UPDATE challenge_attempts
            SET winner_xp = 0
            WHERE winner_xp IS NULL
            """
        )
    )

    bind.execute(
        sa.text(
            """
            UPDATE challenge_attempts
            SET individual_xp = 0
            WHERE individual_xp IS NULL
            """
        )
    )

    bind.execute(
        sa.text(
            """
            UPDATE challenge_attempts
            SET group_xp = 0
            WHERE group_xp IS NULL
            """
        )
    )

    # Existing legacy rows may not have an attempt reference. Generate a
    # deterministic unique reference from the immutable attempt ID.
    bind.execute(
        sa.text(
            """
            UPDATE challenge_attempts
            SET attempt_reference = 'legacy-attempt-' || id
            WHERE attempt_reference IS NULL
            """
        )
    )

    # Remove the old physical unique index if it exists. The SQLAlchemy model
    # represents attempt_reference uniqueness with unique=True, not index=True.
    existing_indexes = _existing_indexes(bind, "challenge_attempts")

    if "uq_challenge_attempts_attempt_reference" in existing_indexes:
        op.drop_index(
            "uq_challenge_attempts_attempt_reference",
            table_name="challenge_attempts",
        )

    # Make the model-required fields NOT NULL and add the missing FK.
    with op.batch_alter_table("challenge_attempts") as batch_op:
        batch_op.alter_column(
            "attempt_reference",
            existing_type=sa.String(length=100),
            nullable=False,
        )

        batch_op.alter_column(
            "status",
            existing_type=sa.String(length=30),
            nullable=False,
        )

        batch_op.alter_column(
            "elite",
            existing_type=sa.Boolean(),
            nullable=False,
        )

        batch_op.alter_column(
            "winner",
            existing_type=sa.Boolean(),
            nullable=False,
        )

        batch_op.alter_column(
            "participation_xp",
            existing_type=sa.Integer(),
            nullable=False,
        )

        batch_op.alter_column(
            "elite_xp",
            existing_type=sa.Integer(),
            nullable=False,
        )

        batch_op.alter_column(
            "winner_xp",
            existing_type=sa.Integer(),
            nullable=False,
        )

        batch_op.alter_column(
            "individual_xp",
            existing_type=sa.Integer(),
            nullable=False,
        )

        batch_op.alter_column(
            "group_xp",
            existing_type=sa.Integer(),
            nullable=False,
        )

        # Only add this FK if it is not already present.
        foreign_keys = sa.inspect(bind).get_foreign_keys(
            "challenge_attempts"
        )

        verified_by_fk_exists = any(
            fk.get("constrained_columns") == ["verified_by"]
            and fk.get("referred_table") == "users"
            and fk.get("referred_columns") == ["id"]
            for fk in foreign_keys
        )

        if not verified_by_fk_exists:
            batch_op.create_foreign_key(
                "fk_challenge_attempts_verified_by_users",
                "users",
                ["verified_by"],
                ["id"],
            )

        batch_op.create_unique_constraint(
            "uq_challenge_attempts_attempt_reference",
            ["attempt_reference"],
        )

    # status is queried by the challenge workflow.
    existing_indexes = _existing_indexes(bind, "challenge_attempts")

    if "ix_challenge_attempts_status" not in existing_indexes:
        op.create_index(
            "ix_challenge_attempts_status",
            "challenge_attempts",
            ["status"],
            unique=False,
        )


def downgrade() -> None:
    bind = op.get_bind()

    existing_indexes = _existing_indexes(bind, "challenge_attempts")

    if "ix_challenge_attempts_status" in existing_indexes:
        op.drop_index(
            "ix_challenge_attempts_status",
            table_name="challenge_attempts",
        )

    with op.batch_alter_table("challenge_attempts") as batch_op:
        batch_op.drop_constraint(
            "uq_challenge_attempts_attempt_reference",
            type_="unique",
        )

        batch_op.drop_constraint(
            "fk_challenge_attempts_verified_by_users",
            type_="foreignkey",
        )

        for name in reversed(list(CHALLENGE_ATTEMPT_COLUMNS)):
            # Only drop columns that belong to this migration. This is safe
            # for databases created from the old initial schema.
            if name in _existing_columns(bind, "challenge_attempts"):
                batch_op.drop_column(name)
