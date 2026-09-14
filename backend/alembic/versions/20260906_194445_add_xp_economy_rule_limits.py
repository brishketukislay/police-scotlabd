"""Add configurable XP economy rule limits.

Revision ID: 202609061944
Revises: 31122dcdbc38
Create Date: 2026-09-06 19:44:45
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "202609061944"
down_revision: Union[str, Sequence[str], None] = "add_player_programme"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = {
        column["name"]
        for column in inspector.get_columns("point_rules")
    }

    # The previous failed migration may have successfully added these
    # columns before failing on SQLite constraint handling. Make this
    # migration idempotent for that partially-applied state.
    if "individual_award_cap" not in columns:
        op.add_column(
            "point_rules",
            sa.Column(
                "individual_award_cap",
                sa.Integer(),
                nullable=True,
            ),
        )

    if "group_award_cap" not in columns:
        op.add_column(
            "point_rules",
            sa.Column(
                "group_award_cap",
                sa.Integer(),
                nullable=True,
            ),
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    columns = {
        column["name"]
        for column in inspector.get_columns("point_rules")
    }

    if "group_award_cap" in columns:
        op.drop_column("point_rules", "group_award_cap")

    if "individual_award_cap" in columns:
        op.drop_column("point_rules", "individual_award_cap")
