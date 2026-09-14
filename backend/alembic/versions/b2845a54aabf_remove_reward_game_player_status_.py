"""remove reward game player status uniqueness

Revision ID: b2845a54aabf
Revises: 20260906_phase6_challenge_attempt_schema
"""

from typing import Sequence, Union

from alembic import op


revision: str = "b2845a54aabf"
down_revision: Union[str, Sequence[str], None] = (
    "20260906_phase6_challenge_attempt_schema"
)
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("player_reward_games") as batch_op:
        batch_op.drop_constraint(
            "uq_reward_game_player_status",
            type_="unique",
        )


def downgrade() -> None:
    with op.batch_alter_table("player_reward_games") as batch_op:
        batch_op.create_unique_constraint(
            "uq_reward_game_player_status",
            ["game_id", "player_id", "status"],
        )
