"""add xp transaction reference uniqueness

Revision ID: c9787fd3cc7d
Revises: 020634c8f304
Create Date: 2026-09-04 16:48:05.019524

"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c9787fd3cc7d"
down_revision: Union[str, Sequence[str], None] = "020634c8f304"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("xp_transactions") as batch_op:
        batch_op.create_unique_constraint(
            "uq_xp_transaction_reference",
            ["reference_type", "reference_id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("xp_transactions") as batch_op:
        batch_op.drop_constraint(
            "uq_xp_transaction_reference",
            type_="unique",
        )
