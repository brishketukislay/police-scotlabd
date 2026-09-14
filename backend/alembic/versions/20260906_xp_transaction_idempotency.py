"""add XP transaction idempotency

Revision ID: 20260906_xp_transaction_idempotency
Revises: b2845a54aabf
Create Date: 2026-09-06
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20260906_xp_transaction_idempotency"
down_revision = "b2845a54aabf"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # The column may already exist in databases created from the
    # current ORM schema before this migration was recorded.
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {
        column["name"]
        for column in inspector.get_columns("xp_transactions")
    }

    if "idempotency_key" not in columns:
        op.add_column(
            "xp_transactions",
            sa.Column(
                "idempotency_key",
                sa.String(length=255),
                nullable=True,
            ),
        )

    # Legacy XP transactions have NULL keys and are unaffected.
    # Every non-NULL idempotency key must identify exactly one
    # logical XP transaction.
    op.create_index(
        "ux_xp_transactions_idempotency_key",
        "xp_transactions",
        ["idempotency_key"],
        unique=True,
        postgresql_where=sa.text("idempotency_key IS NOT NULL"),
        sqlite_where=sa.text("idempotency_key IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "ux_xp_transactions_idempotency_key",
        table_name="xp_transactions",
    )

    op.drop_column(
        "xp_transactions",
        "idempotency_key",
    )
