from pathlib import Path
import sqlite3

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from app.core.config import settings


DATABASE_URL = settings.database_url


# Resolve the default SQLite database relative to this project instead of
# relying on the process working directory.
if DATABASE_URL == "sqlite:///./youth_platform.db":
    DEFAULT_DATABASE_PATH = (
        Path(__file__).resolve().parents[2] / "youth_platform.db"
    )
    DATABASE_URL = f"sqlite:///{DEFAULT_DATABASE_PATH}"


connect_args: dict[str, object] = {}

if DATABASE_URL.startswith("sqlite"):
    connect_args = {
        "check_same_thread": False,
        "timeout": 30,
    }


engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
)


if DATABASE_URL.startswith("sqlite"):

    @event.listens_for(engine, "connect")
    def _configure_sqlite_connection(
        dbapi_connection: sqlite3.Connection,
        connection_record,
    ) -> None:
        """
        Configure SQLite without changing journal mode during connection
        startup.

        In particular, do not execute:
            PRAGMA journal_mode = WAL

        here. Changing journal mode is a database-level operation and can
        create unnecessary contention or interact badly with stale WAL/SHM
        files during local development.

        SQLite's normal rollback journal is sufficient for this development
        application and is safer while the database is being stabilized.
        """

        cursor = dbapi_connection.cursor()

        cursor.execute("PRAGMA busy_timeout = 30000")
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.execute("PRAGMA synchronous = NORMAL")

        cursor.close()


SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_db():
    """
    FastAPI database dependency.
    """

    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


__all__ = [
    "DATABASE_URL",
    "SessionLocal",
    "engine",
    "get_db",
]
