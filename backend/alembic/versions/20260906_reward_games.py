"""add scratch cards and reward wheels

Revision ID: 20260906_reward_games
Revises: c9787fd3cc7d
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "20260906_reward_games"
down_revision: Union[str, Sequence[str], None] = "c9787fd3cc7d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "reward_games",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "programme_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "name",
            sa.String(length=200),
            nullable=False,
        ),
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
        ),
        sa.Column(
            "game_type",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "prize_values",
            sa.JSON(),
            nullable=False,
        ),
        sa.Column(
            "starts_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "ends_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "active",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "show_upcoming",
            sa.Boolean(),
            nullable=False,
        ),
        sa.Column(
            "created_by_user_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["programme_id"],
            ["programmes.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["created_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_reward_games_programme_id",
        "reward_games",
        ["programme_id"],
    )
    op.create_index(
        "ix_reward_games_game_type",
        "reward_games",
        ["game_type"],
    )
    op.create_index(
        "ix_reward_games_starts_at",
        "reward_games",
        ["starts_at"],
    )
    op.create_index(
        "ix_reward_games_ends_at",
        "reward_games",
        ["ends_at"],
    )
    op.create_index(
        "ix_reward_games_active",
        "reward_games",
        ["active"],
    )

    op.create_table(
        "player_reward_games",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column(
            "game_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "player_id",
            sa.Integer(),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "awarded_xp",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "xp_transaction_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "played_at",
            sa.DateTime(),
            nullable=True,
        ),
        sa.Column(
            "granted_by_user_id",
            sa.Integer(),
            nullable=True,
        ),
        sa.Column(
            "granted_at",
            sa.DateTime(),
            nullable=False,
        ),
        sa.Column(
            "play_metadata",
            sa.JSON(),
            nullable=True,
        ),
        sa.ForeignKeyConstraint(
            ["game_id"],
            ["reward_games.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["player_id"],
            ["players.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["xp_transaction_id"],
            ["xp_transactions.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["granted_by_user_id"],
            ["users.id"],
            ondelete="SET NULL",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "game_id",
            "player_id",
            "status",
            name="uq_reward_game_player_status",
        ),
    )

    op.create_index(
        "ix_player_reward_games_game_id",
        "player_reward_games",
        ["game_id"],
    )
    op.create_index(
        "ix_player_reward_games_player_id",
        "player_reward_games",
        ["player_id"],
    )
    op.create_index(
        "ix_player_reward_games_status",
        "player_reward_games",
        ["status"],
    )
    op.create_index(
        "ix_player_reward_games_xp_transaction_id",
        "player_reward_games",
        ["xp_transaction_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_player_reward_games_xp_transaction_id",
        table_name="player_reward_games",
    )
    op.drop_index(
        "ix_player_reward_games_status",
        table_name="player_reward_games",
    )
    op.drop_index(
        "ix_player_reward_games_player_id",
        table_name="player_reward_games",
    )
    op.drop_index(
        "ix_player_reward_games_game_id",
        table_name="player_reward_games",
    )

    op.drop_table("player_reward_games")

    op.drop_index(
        "ix_reward_games_active",
        table_name="reward_games",
    )
    op.drop_index(
        "ix_reward_games_ends_at",
        table_name="reward_games",
    )
    op.drop_index(
        "ix_reward_games_starts_at",
        table_name="reward_games",
    )
    op.drop_index(
        "ix_reward_games_game_type",
        table_name="reward_games",
    )
    op.drop_index(
        "ix_reward_games_programme_id",
        table_name="reward_games",
    )

    op.drop_table("reward_games")
