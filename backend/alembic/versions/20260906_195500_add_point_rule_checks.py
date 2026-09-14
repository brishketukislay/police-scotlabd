"""Add PointRule CHECK constraints.

Revision ID: 202609061955
Revises: 202609061944
Create Date: 2026-09-06
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "202609061955"
down_revision: Union[str, Sequence[str], None] = "202609061944"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    # SQLite requires a table rebuild to add CHECK constraints.
    # Explicit SQL avoids Alembic batch-mode dependency sorting,
    # which previously hit a circular dependency for the two new
    # award-cap columns.
    bind.exec_driver_sql(
        """
        CREATE TABLE _point_rules_with_checks (
            id INTEGER NOT NULL,
            programme_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            code VARCHAR(100) NOT NULL,
            description TEXT,
            individual_xp INTEGER NOT NULL,
            group_xp INTEGER NOT NULL,
            weekly_cap INTEGER,
            enabled BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            awards_per_week FLOAT DEFAULT '0' NOT NULL,
            individual_award_cap INTEGER,
            group_award_cap INTEGER,

            PRIMARY KEY (id),

            FOREIGN KEY(programme_id)
                REFERENCES programmes (id),

            CONSTRAINT uq_programme_point_rule_code
                UNIQUE (programme_id, code),

            CONSTRAINT ck_point_rule_individual_xp_non_negative
                CHECK (individual_xp >= 0),

            CONSTRAINT ck_point_rule_group_xp_non_negative
                CHECK (group_xp >= 0),

            CONSTRAINT ck_point_rule_weekly_cap_positive
                CHECK (weekly_cap IS NULL OR weekly_cap > 0),

            CONSTRAINT ck_point_rule_awards_per_week_non_negative
                CHECK (awards_per_week >= 0),

            CONSTRAINT ck_point_rule_individual_award_cap_positive
                CHECK (
                    individual_award_cap IS NULL
                    OR individual_award_cap > 0
                ),

            CONSTRAINT ck_point_rule_group_award_cap_positive
                CHECK (
                    group_award_cap IS NULL
                    OR group_award_cap > 0
                ),

            CONSTRAINT ck_point_rule_has_positive_reward
                CHECK (
                    individual_xp > 0
                    OR group_xp > 0
                )
        )
        """
    )

    bind.exec_driver_sql(
        """
        INSERT INTO _point_rules_with_checks (
            id,
            programme_id,
            name,
            code,
            description,
            individual_xp,
            group_xp,
            weekly_cap,
            enabled,
            created_at,
            updated_at,
            awards_per_week,
            individual_award_cap,
            group_award_cap
        )
        SELECT
            id,
            programme_id,
            name,
            code,
            description,
            individual_xp,
            group_xp,
            weekly_cap,
            enabled,
            created_at,
            updated_at,
            awards_per_week,
            individual_award_cap,
            group_award_cap
        FROM point_rules
        """
    )

    # Preserve the existing index before replacing the table.
    bind.exec_driver_sql(
        "DROP INDEX IF EXISTS ix_point_rules_programme_id"
    )

    bind.exec_driver_sql(
        "DROP TABLE point_rules"
    )

    bind.exec_driver_sql(
        """
        ALTER TABLE _point_rules_with_checks
        RENAME TO point_rules
        """
    )

    bind.exec_driver_sql(
        """
        CREATE INDEX ix_point_rules_programme_id
        ON point_rules (programme_id)
        """
    )


def downgrade() -> None:
    bind = op.get_bind()

    bind.exec_driver_sql(
        """
        CREATE TABLE _point_rules_without_checks (
            id INTEGER NOT NULL,
            programme_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            code VARCHAR(100) NOT NULL,
            description TEXT,
            individual_xp INTEGER NOT NULL,
            group_xp INTEGER NOT NULL,
            weekly_cap INTEGER,
            enabled BOOLEAN NOT NULL,
            created_at DATETIME NOT NULL,
            updated_at DATETIME NOT NULL,
            awards_per_week FLOAT DEFAULT '0' NOT NULL,
            individual_award_cap INTEGER,
            group_award_cap INTEGER,

            PRIMARY KEY (id),

            FOREIGN KEY(programme_id)
                REFERENCES programmes (id),

            CONSTRAINT uq_programme_point_rule_code
                UNIQUE (programme_id, code)
        )
        """
    )

    bind.exec_driver_sql(
        """
        INSERT INTO _point_rules_without_checks (
            id,
            programme_id,
            name,
            code,
            description,
            individual_xp,
            group_xp,
            weekly_cap,
            enabled,
            created_at,
            updated_at,
            awards_per_week,
            individual_award_cap,
            group_award_cap
        )
        SELECT
            id,
            programme_id,
            name,
            code,
            description,
            individual_xp,
            group_xp,
            weekly_cap,
            enabled,
            created_at,
            updated_at,
            awards_per_week,
            individual_award_cap,
            group_award_cap
        FROM point_rules
        """
    )

    bind.exec_driver_sql(
        "DROP INDEX IF EXISTS ix_point_rules_programme_id"
    )

    bind.exec_driver_sql(
        "DROP TABLE point_rules"
    )

    bind.exec_driver_sql(
        """
        ALTER TABLE _point_rules_without_checks
        RENAME TO point_rules
        """
    )

    bind.exec_driver_sql(
        """
        CREATE INDEX ix_point_rules_programme_id
        ON point_rules (programme_id)
        """
    )
