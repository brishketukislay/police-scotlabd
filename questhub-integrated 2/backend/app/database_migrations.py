from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def column_exists(
    engine: Engine,
    table_name: str,
    column_name: str,
) -> bool:
    inspector = inspect(engine)

    if not inspector.has_table(table_name):
        return False

    return any(
        column["name"] == column_name
        for column in inspector.get_columns(table_name)
    )


def index_exists(
    engine: Engine,
    table_name: str,
    index_name: str,
) -> bool:
    inspector = inspect(engine)

    if not inspector.has_table(table_name):
        return False

    return any(
        index["name"] == index_name
        for index in inspector.get_indexes(table_name)
    )


def add_xp_transaction_group_id(engine: Engine) -> None:
    """
    Backwards-compatible migration for existing pilot databases.
    """

    if column_exists(
        engine,
        "xp_transactions",
        "group_id",
    ):
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE xp_transactions
                ADD COLUMN group_id INTEGER
                """
            )
        )

        connection.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS
                ix_xp_transactions_group_id
                ON xp_transactions (group_id)
                """
            )
        )


def add_xp_transaction_idempotency_key(
    engine: Engine,
) -> None:
    """
    Add an optional idempotency key without breaking historical rows.

    Historical transactions cannot safely be assigned synthetic keys based
    on business semantics, so the column is nullable for old records.
    New application-created transactions may populate it.
    """

    if column_exists(
        engine,
        "xp_transactions",
        "idempotency_key",
    ):
        return

    with engine.begin() as connection:
        connection.execute(
            text(
                """
                ALTER TABLE xp_transactions
                ADD COLUMN idempotency_key VARCHAR(255)
                """
            )
        )

        connection.execute(
            text(
                """
                CREATE UNIQUE INDEX IF NOT EXISTS
                ux_xp_transactions_idempotency_key
                ON xp_transactions (idempotency_key)
                WHERE idempotency_key IS NOT NULL
                """
            )
        )


def run_migrations(engine: Engine) -> None:
    add_xp_transaction_group_id(engine)
    add_xp_transaction_idempotency_key(engine)
    create_xp_balance_tables(engine)


def create_xp_balance_tables(engine: Engine) -> None:
    """
    Create XP balance projection tables for existing databases.

    These tables are derived from the XP transaction ledger and are safe
    to create when upgrading an existing pilot database.
    """

    from .db.models.xp_balance import (
        GroupXPBalance,
        PlayerXPBalance,
    )

    PlayerXPBalance.__table__.create(
        bind=engine,
        checkfirst=True,
    )

    GroupXPBalance.__table__.create(
        bind=engine,
        checkfirst=True,
    )
