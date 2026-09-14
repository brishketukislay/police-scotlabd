from __future__ import annotations

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Base class for every SQLAlchemy ORM model.

    Models should inherit from this class rather than creating their own
    declarative bases. This gives Alembic one metadata collection to inspect
    when generating migrations.
    """

    pass
