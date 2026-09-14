"""require group id for group penalties

Revision ID: 31122dcdbc38
Revises: 20260906_xp_transaction_idempotency
Create Date: 2026-09-06
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "31122dcdbc38"
down_revision = "20260906_xp_transaction_idempotency"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("group_penalties") as batch_op:
        batch_op.alter_column(
            "group_id",
            existing_type=sa.Integer(),
            nullable=False,
        )


def downgrade() -> None:
    with op.batch_alter_table("group_penalties") as batch_op:
        batch_op.alter_column(
            "group_id",
            existing_type=sa.Integer(),
            nullable=True,
        )
