from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context
from alembic.operations.ops import ModifyTableOps, AddConstraintOp

from app.db.base import Base
import app.db.models  # noqa: F401


config = context.config


if config.config_file_name is not None:
    fileConfig(config.config_file_name)


target_metadata = Base.metadata


# Tables intentionally maintained outside SQLAlchemy's declarative metadata.
#
# recognition_tokens is currently accessed by app/routers/recognition.py using
# raw SQL, so Alembic must not interpret its absence from Base.metadata as a
# request to DROP the table.
#
# transaction_debug_test is a local/debug table and is likewise excluded from
# Alembic's schema comparison.
LEGACY_ALEMBIC_TABLES = {
    "recognition_tokens",
    "transaction_debug_test",
}


def include_object(object, name, type_, reflected, compare_to):
    if type_ == "table" and reflected and name in LEGACY_ALEMBIC_TABLES:
        return False

    # SQLite reflects existing CHECK constraints without their names.
    # The checkconstraint_byname autogenerate plugin then incorrectly sees
    # the named SQLAlchemy constraints as new constraints. These constraints
    # already exist in point_rules, so exclude them from autogeneration.
    if (
        type_ == "check_constraint"
        and reflected
        and getattr(object, "table", None) is not None
        and object.table.name == "point_rules"
    ):
        return False

    # SQLite reflects CHECK constraints without names.
    # Existing unnamed CHECK constraints are handled separately by the
    # custom comparator below.
    if type_ == "check_constraint" and reflected and name is None:
        return False

    # The idempotency index is intentionally database-managed.
    # It is a unique partial index and is not represented in SQLAlchemy
    # declarative metadata, so Alembic must not try to remove it.
    if (
        type_ == "index"
        and reflected
        and name == "ux_xp_transactions_idempotency_key"
    ):
        return False

    return True


def compare_type(context, inspected_column, metadata_column, inspected_type, metadata_type):
    """
    SQLite stores SQLAlchemy Enum(native_enum=False) values as VARCHAR.

    The application intentionally models these values as Python enums, but
    that should not produce a migration every time Alembic compares the
    SQLite VARCHAR representation with the SQLAlchemy Enum representation.
    """
    if (
        inspected_column.name == "game_type"
        and inspected_column.table.name == "reward_games"
    ):
        return False

    if (
        inspected_column.name == "status"
        and inspected_column.table.name == "player_reward_games"
    ):
        return False

    return None


def process_revision_directives(context, revision, directives):
    """
    Remove SQLite constraint operations that are already represented in the
    existing point_rules database schema.

    SQLite does not preserve CHECK constraint names during reflection, and
    Alembic's checkconstraint_byname plugin therefore reports these existing
    constraints as new ones.
    """
    if not directives:
        return

    script = directives[0]

    def filter_ops(container):
        if not hasattr(container, "ops"):
            return

        filtered = []

        for op in container.ops:
            if isinstance(op, ModifyTableOps):
                filter_ops(op)
                if op.ops:
                    filtered.append(op)
                continue

            if isinstance(op, AddConstraintOp):
                constraint = op.to_constraint()
                table = getattr(constraint, "table", None)
                table_name = getattr(table, "name", None)

                if table_name == "point_rules":
                    # All current point_rules constraints already exist.
                    continue

            filtered.append(op)

        container.ops[:] = filtered

    filter_ops(script.upgrade_ops)
    filter_ops(script.downgrade_ops)


def run_migrations_offline() -> None:
    """Run migrations without a database connection."""

    url = config.get_main_option("sqlalchemy.url")

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={
            "paramstyle": "named",
        },
        compare_type=compare_type,
        compare_server_default=False,
        autogenerate_plugins=AUTOGENERATE_PLUGINS,
        include_object=include_object,
        process_revision_directives=process_revision_directives,
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using a live database connection."""

    connectable = engine_from_config(
        config.get_section(
            config.config_ini_section,
            {},
        ),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=compare_type,
            compare_server_default=False,
            include_object=include_object,
            process_revision_directives=process_revision_directives,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
