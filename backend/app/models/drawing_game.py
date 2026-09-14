from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class DrawingGame(Base):
    __tablename__ = "drawing_games"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # circle | square | triangle
    shape: Mapped[str] = mapped_column(String(30), nullable=False)

    # Configuration consumed by the frontend renderer.
    config: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    # Ordered:
    # [{"min": 0, "max": 49, "xp": 10}, ...]
    xp_brackets: Mapped[list[dict[str, int]]] = mapped_column(
        JSON,
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )


class DrawingGameAssignment(Base):
    __tablename__ = "drawing_game_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    game_id: Mapped[int] = mapped_column(
        ForeignKey("drawing_games.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    assigned_by_user_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Useful when assignment came from a group.
    source_group_id: Mapped[int | None] = mapped_column(
        ForeignKey("groups.id", ondelete="SET NULL"),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="assigned",
        index=True,
    )

    assigned_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "game_id",
            "player_id",
            name="uq_drawing_game_player_assignment",
        ),
    )


class DrawingGameAttempt(Base):
    __tablename__ = "drawing_game_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)

    assignment_id: Mapped[int] = mapped_column(
        ForeignKey(
            "drawing_game_assignments.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    accuracy_percent: Mapped[float] = mapped_column(
        nullable=False,
    )

    awarded_xp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    # Small diagnostic payload, not the complete raw drawing.
    result_metadata: Mapped[dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    xp_transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("xp_transactions.id", ondelete="SET NULL"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )
