"""add awards_per_week to point_rules

Revision ID: 20260906_point_rule_awards_per_week
Revises: 20260906_reward_games
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260906_point_rule_awards_per_week"
down_revision: Union[str, Sequence[str], None] = "20260906_reward_games"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "point_rules",
        sa.Column(
            "awards_per_week",
            sa.Float(),
            nullable=False,
            server_default="0",
        ),
    )


def downgrade() -> None:
    op.drop_column(
        "point_rules",
        "awards_per_week",
    )
