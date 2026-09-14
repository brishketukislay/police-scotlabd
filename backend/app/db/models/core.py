"""
Digital Youth Platform - Domain Models

The application is intentionally configuration-driven.

Important architectural rules:

1. XP is recorded as immutable ledger transactions.
2. Individual XP and collective/group XP are separate values.
3. Lifetime XP is never reset.
4. Skill-tree progress can reset without destroying historical XP.
5. Public player identity contains ONLY a gamertag + avatar.
6. Real-world identity belongs to the User record and is never exposed
   through public/player-facing APIs.
7. Programme, map, phase, theme, rules, rewards and challenges are
   configurable records rather than hard-coded application constants.
8. Admin/staff actions should create AuditLog records.
9. Deleting a player should normally be implemented as deactivation/anonymisation
   rather than physical deletion because the pilot requires an audit trail.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..base import Base


# ============================================================================
# COMMON
# ============================================================================


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )


# ============================================================================
# AUTHENTICATION / AUTHORISATION
# ============================================================================


class User(Base, TimestampMixin):
    """
    Internal account.

    A User is deliberately separate from Player because:
    - staff are users but not players;
    - player public identity must remain pseudonymous;
    - personally identifiable information must never be returned by
      public leaderboard endpoints.
    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="player",
        index=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    last_login_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Optional staff metadata.
    #
    # These are intentionally not connected to the public player profile.
    # ------------------------------------------------------------------

    display_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------

    player: Mapped[Optional["Player"]] = relationship(
        "Player",
        back_populates="user",
        uselist=False,
    )

    audit_logs: Mapped[list["AuditLog"]] = relationship(
        "AuditLog",
        back_populates="user",
    )


# ============================================================================
# PROGRAMME
# ============================================================================


class Programme(Base, TimestampMixin):
    """
    A complete delivery programme/pilot.

    Keeping this configurable allows the same application to support:
    - Cumbernauld;
    - another town;
    - another cohort;
    - a future programme;
    - a different XP target;
    without changing application code.
    """

    __tablename__ = "programmes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    # Collective jackpot target.
    target_xp: Mapped[int] = mapped_column(
        Integer,
        default=1_500_000,
        nullable=False,
    )

    # Optional operational target used by staff dashboards.
    weekly_target_xp: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Maximum percentage of collective pool that one exceptional
    # group penalty can remove.
    max_group_penalty_percent: Mapped[float] = mapped_column(
        Float,
        default=10.0,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Current presentation configuration
    # ------------------------------------------------------------------

    active_theme_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("themes.id"),
        nullable=True,
    )

    active_map_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("maps.id"),
        nullable=True,
    )

    active_phase_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("phases.id"),
        nullable=True,
    )

    themes: Mapped[list["Theme"]] = relationship(
        "Theme",
        back_populates="programme",
        foreign_keys="Theme.programme_id",
    )

    maps: Mapped[list["GameMap"]] = relationship(
    "GameMap",
    back_populates="programme",
    foreign_keys="GameMap.programme_id",
)


    phases: Mapped[list["Phase"]] = relationship(
    "Phase",
    back_populates="programme",
    foreign_keys="Phase.programme_id",
)


    groups: Mapped[list["YouthGroup"]] = relationship(
        "YouthGroup",
        back_populates="programme",
    )


# ============================================================================
# THEMING
# ============================================================================


class Theme(Base, TimestampMixin):
    """
    Admin-configurable application theme.

    Admins can create multiple themes and switch the programme's
    active theme without deploying new frontend code.
    """

    __tablename__ = "themes"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    primary: Mapped[str] = mapped_column(
        String(20),
        default="#18775B",
        nullable=False,
    )

    secondary: Mapped[str] = mapped_column(
        String(20),
        default="#0F513C",
        nullable=False,
    )

    accent: Mapped[str] = mapped_column(
        String(20),
        default="#43B98B",
        nullable=False,
    )

    background: Mapped[str] = mapped_column(
        String(20),
        default="#F3F7F5",
        nullable=False,
    )

    surface: Mapped[str] = mapped_column(
        String(20),
        default="#FFFFFF",
        nullable=False,
    )

    text: Mapped[str] = mapped_column(
        String(20),
        default="#17221E",
        nullable=False,
    )

    # Optional richer UI configuration.
    logo_url: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    font_family: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    programme: Mapped[Optional["Programme"]] = relationship(
        "Programme",
        back_populates="themes",
        foreign_keys=[programme_id],
    )


# ============================================================================
# MAP
# ============================================================================


class GameMap(Base, TimestampMixin):
    """
    Configurable map.

    The map is not hard-coded as "Cumbernauld". An administrator can create
    another map/location later.

    background_image can point at an SVG, raster image or externally hosted
    asset. Map coordinates are stored as percentages from 0-1.
    """

    __tablename__ = "maps"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    background_image: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    programme: Mapped[Optional["Programme"]] = relationship(
    "Programme",
    back_populates="maps",
    foreign_keys=[programme_id],
)


    locations: Mapped[list["MapLocation"]] = relationship(
        "MapLocation",
        back_populates="map",
        cascade="all, delete-orphan",
    )


class MapLocation(Base, TimestampMixin):
    """
    Point of interest on a game map.

    x/y are percentages represented as floats in the range 0..1.
    """

    __tablename__ = "map_locations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    map_id: Mapped[int] = mapped_column(
        ForeignKey("maps.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    x: Mapped[float] = mapped_column(
        Float,
        default=0.5,
        nullable=False,
    )

    y: Mapped[float] = mapped_column(
        Float,
        default=0.5,
        nullable=False,
    )

    icon: Mapped[str] = mapped_column(
        String(50),
        default="pin",
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    map: Mapped["GameMap"] = relationship(
        "GameMap",
        back_populates="locations",
    )

    phase_links: Mapped[list["PhaseLocation"]] = relationship(
        "PhaseLocation",
        back_populates="location",
    )

    __table_args__ = (
        CheckConstraint("x >= 0 AND x <= 1", name="ck_map_location_x"),
        CheckConstraint("y >= 0 AND y <= 1", name="ck_map_location_y"),
    )


# ============================================================================
# PHASES
# ============================================================================


class Phase(Base, TimestampMixin):
    """
    A programme phase/theme such as:
    - Art
    - Sport
    - Civic Safety
    - Road Safety
    """

    __tablename__ = "phases"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    icon: Mapped[str] = mapped_column(
        String(50),
        default="star",
        nullable=False,
    )

    colour: Mapped[str] = mapped_column(
        String(20),
        default="#18775B",
        nullable=False,
    )

    start_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    end_date: Mapped[Optional[date]] = mapped_column(
        Date,
        nullable=True,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    programme: Mapped["Programme"] = relationship(
    "Programme",
    back_populates="phases",
    foreign_keys=[programme_id],
)


    locations: Mapped[list["PhaseLocation"]] = relationship(
        "PhaseLocation",
        back_populates="phase",
        cascade="all, delete-orphan",
    )

    challenges: Mapped[list["Challenge"]] = relationship(
        "Challenge",
        back_populates="phase",
    )

    resources: Mapped[list["Resource"]] = relationship(
        "Resource",
        back_populates="phase",
    )


class PhaseLocation(Base):
    """
    Associates a phase with one or more locations on the active map.
    """

    __tablename__ = "phase_locations"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    phase_id: Mapped[int] = mapped_column(
        ForeignKey("phases.id"),
        nullable=False,
        index=True,
    )

    location_id: Mapped[int] = mapped_column(
        ForeignKey("map_locations.id"),
        nullable=False,
        index=True,
    )

    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    phase: Mapped["Phase"] = relationship(
        "Phase",
        back_populates="locations",
    )

    location: Mapped["MapLocation"] = relationship(
        "MapLocation",
        back_populates="phase_links",
    )

    __table_args__ = (
        UniqueConstraint(
            "phase_id",
            "location_id",
            name="uq_phase_location",
        ),
    )


# ============================================================================
# GROUPS / COHORTS
# ============================================================================


class YouthGroup(Base, TimestampMixin):
    """
    Internal delivery group.

    Groups can be used by youth workers for sessions, while the public
    leaderboard can aggregate everyone into the programme cohort.
    """

    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    programme: Mapped["Programme"] = relationship(
        "Programme",
        back_populates="groups",
    )

    players: Mapped[list["Player"]] = relationship(
        "Player",
        back_populates="group",
    )


# ============================================================================
# PLAYER
# ============================================================================


class Player(Base, TimestampMixin):
    """
    Public-facing participant record.

    IMPORTANT:
    gamertag and avatar are the only fields that should ever be returned
    from a public leaderboard.

    No real name, photograph, email address, phone number or other PII
    belongs here.
    """

    __tablename__ = "players"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
        index=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("groups.id"),
        nullable=True,
        index=True,
    )

    gamertag: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    avatar: Mapped[str] = mapped_column(
        String(100),
        default="avatar-01",
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
    )

    # Public profile can be hidden temporarily by authorised staff.
    public_visible: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    # Used when staff suspend participation without deleting the account.
    suspended: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="player",
    )

    attendance_token: Mapped[Optional["PlayerAttendanceToken"]] = relationship(
        "PlayerAttendanceToken",
        back_populates="player",
        uselist=False,
        cascade="all, delete-orphan",
    )

    group: Mapped[Optional["YouthGroup"]] = relationship(
        "YouthGroup",
        back_populates="players",
    )

    xp_transactions: Mapped[list["XPTransaction"]] = relationship(
        "XPTransaction",
        back_populates="player",
    )

    attendance: Mapped[list["Attendance"]] = relationship(
        "Attendance",
        back_populates="player",
    )

    skill_trees: Mapped[list["SkillTree"]] = relationship(
        "SkillTree",
        back_populates="player",
    )

    badges: Mapped[list["PlayerBadge"]] = relationship(
        "PlayerBadge",
        back_populates="player",
    )

    rewards: Mapped[list["PlayerReward"]] = relationship(
        "PlayerReward",
        back_populates="player",
    )

    community_awards: Mapped[list["CommunityAward"]] = relationship(
        "CommunityAward",
        back_populates="player",
    )

    challenge_attempts: Mapped[list["ChallengeAttempt"]] = relationship(
        "ChallengeAttempt",
        back_populates="player",
    )

    kudos_received: Mapped[list["Kudos"]] = relationship(
        "Kudos",
        foreign_keys="Kudos.recipient_player_id",
        back_populates="recipient",
    )


# ============================================================================
# XP LEDGER
# ============================================================================


class XPTransaction(Base):
    """
    Immutable XP ledger.

    This is the authoritative source for XP.

    amount:
        Change to individual player's XP.

    group_amount:
        Change to collective programme/group pool.

    Examples:

        attendance:
            amount=500
            group_amount=500

        community award:
            amount=5000
            group_amount=5000

        individual penalty:
            amount=-1500
            group_amount=0

        exceptional collective penalty:
            amount=0
            group_amount=-25000

    NEVER update an existing transaction to correct a balance.

    Instead, create a compensating transaction.
    """

    __tablename__ = "xp_transactions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    player_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("players.id"),
        nullable=True,
        index=True,
    )

    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("groups.id"),
        nullable=True,
        index=True,
    )

    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    group_amount: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    transaction_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    # Idempotency key used by the XP service to prevent duplicate awards.
    #
    # Nullable for legacy transactions created before idempotency was added.
    # The database already contains a unique partial index for non-null keys.
    idempotency_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        index=False,
    )

    reason: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    # Optional reference to another domain record.
    reference_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    reference_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    created_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    player: Mapped[Optional["Player"]] = relationship(
        "Player",
        back_populates="xp_transactions",
    )

    __table_args__ = (
        CheckConstraint(
            "amount != 0 OR group_amount != 0",
            name="ck_xp_transaction_non_zero",
        ),
        UniqueConstraint(
            "reference_type",
            "reference_id",
            name="uq_xp_transaction_reference",
        ),
    )


# ============================================================================
# POINT RULES
# ============================================================================


class PointRule(Base, TimestampMixin):
    """
    Database-driven XP economy rule.

    Feature code identifies an action by ``code`` and delegates the
    actual economy configuration to this table.

    Historical XP transactions are never recalculated when a rule changes.
    A rule therefore controls future awards only.

    The rule supports:

    - player XP
    - group XP
    - enable/disable
    - per-player weekly XP cap
    - maximum awards per player per week
    - optional per-award player XP cap
    - optional per-award group XP cap

    A value of NULL means "unlimited / not configured".
    """

    __tablename__ = "point_rules"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    individual_xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    group_xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    weekly_cap: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    awards_per_week: Mapped[float] = mapped_column(
        Float,
        default=0.0,
        server_default="0",
        nullable=False,
    )

    individual_award_cap: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    group_award_cap: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="1",
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "programme_id",
            "code",
            name="uq_programme_point_rule_code",
        ),
        CheckConstraint(
            "individual_xp >= 0",
            name="ck_point_rule_individual_xp_non_negative",
        ),
        CheckConstraint(
            "group_xp >= 0",
            name="ck_point_rule_group_xp_non_negative",
        ),
        CheckConstraint(
            "weekly_cap IS NULL OR weekly_cap > 0",
            name="ck_point_rule_weekly_cap_positive",
        ),
        CheckConstraint(
            "awards_per_week >= 0",
            name="ck_point_rule_awards_per_week_non_negative",
        ),
        CheckConstraint(
            "individual_award_cap IS NULL OR individual_award_cap > 0",
            name="ck_point_rule_individual_award_cap_positive",
        ),
        CheckConstraint(
            "group_award_cap IS NULL OR group_award_cap > 0",
            name="ck_point_rule_group_award_cap_positive",
        ),
        CheckConstraint(
            "individual_xp > 0 OR group_xp > 0",
            name="ck_point_rule_has_positive_reward",
        ),
    )


class PlayerAttendanceToken(Base):
    __tablename__ = "player_attendance_tokens"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(ForeignKey("players.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    rotated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    player: Mapped["Player"] = relationship("Player", back_populates="attendance_token")


# ============================================================================
# ATTENDANCE
# ============================================================================


class AttendanceSession(Base):
    """
    A staff-created attendance session.

    The frontend can display a short-lived code/QR generated from this
    session. This replaces the need for NFC at this stage.
    """

    __tablename__ = "attendance_sessions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("groups.id"),
        nullable=True,
        index=True,
    )

    code: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        unique=True,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    attendances: Mapped[list["Attendance"]] = relationship(
        "Attendance",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class Attendance(Base):
    """
    Individual attendance against a session.

    UniqueConstraint prevents a player repeatedly scanning the same
    attendance code.
    """

    __tablename__ = "attendance"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey("attendance_sessions.id"),
        nullable=False,
        index=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id"),
        nullable=False,
        index=True,
    )

    checked_in_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    xp_awarded: Mapped[int] = mapped_column(
        Integer,
        default=500,
        nullable=False,
    )

    session: Mapped["AttendanceSession"] = relationship(
        "AttendanceSession",
        back_populates="attendances",
    )

    player: Mapped["Player"] = relationship(
        "Player",
        back_populates="attendance",
    )

    __table_args__ = (
        UniqueConstraint(
            "session_id",
            "player_id",
            name="uq_attendance_session_player",
        ),
    )


# ============================================================================
# SKILL TREES
# ============================================================================


class SkillTree(Base, TimestampMixin):
    """
    Current active personal goal.

    Completing a tree does NOT erase lifetime XP.

    Once complete, the youth worker can archive it and create another tree.
    """

    __tablename__ = "skill_trees"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    current_xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    tree_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    player: Mapped["Player"] = relationship(
        "Player",
        back_populates="skill_trees",
    )

    milestones: Mapped[list["SkillMilestone"]] = relationship(
        "SkillMilestone",
        back_populates="skill_tree",
        cascade="all, delete-orphan",
        order_by="SkillMilestone.sort_order",
    )


class SkillMilestone(Base, TimestampMixin):
    """
    One of the three configurable milestones in a skill tree.

    The XP thresholds and rewards are data rather than hard-coded logic.
    """

    __tablename__ = "skill_milestones"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    skill_tree_id: Mapped[int] = mapped_column(
        ForeignKey("skill_trees.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    required_xp: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    reward_description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    skill_tree: Mapped["SkillTree"] = relationship(
        "SkillTree",
        back_populates="milestones",
    )


# ============================================================================
# BADGES
# ============================================================================


class Badge(Base, TimestampMixin):
    """
    Badge definition.

    This is separate from PlayerBadge because the same badge can be earned
    by many players.
    """

    __tablename__ = "badges"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    colour: Mapped[str] = mapped_column(
        String(20),
        default="#CD7F32",
        nullable=False,
    )

    icon: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    xp_bonus: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    group_xp_bonus: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "programme_id",
            "code",
            name="uq_programme_badge_code",
        ),
    )


class PlayerBadge(Base):
    """
    An earned badge.
    """

    __tablename__ = "player_badges"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id"),
        nullable=False,
        index=True,
    )

    badge_id: Mapped[int] = mapped_column(
        ForeignKey("badges.id"),
        nullable=False,
        index=True,
    )

    earned_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    player: Mapped["Player"] = relationship(
        "Player",
        back_populates="badges",
    )

    badge: Mapped["Badge"] = relationship(
        "Badge",
    )

    __table_args__ = (
        UniqueConstraint(
            "player_id",
            "badge_id",
            name="uq_player_badge",
        ),
    )


# ============================================================================
# REWARDS
# ============================================================================


class Reward(Base, TimestampMixin):
    """
    Reward definition.

    Examples:
    - £5 Love2shop
    - £10 Love2shop
    - physical mystery prize
    - group milestone prize

    The application does not assume every reward is monetary.
    """

    __tablename__ = "rewards"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    reward_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="individual",
    )

    # Monetary value where relevant.
    value: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False,
    )

    currency: Mapped[str] = mapped_column(
        String(10),
        default="GBP",
        nullable=False,
    )

    # Optional XP threshold.
    xp_threshold: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    # Optional milestone/badge reference.
    badge_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("badges.id"),
        nullable=True,
    )

    # Used for mystery prizes.
    mystery: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )


class PlayerReward(Base):
    """
    Reward actually granted to a player.

    This is separate from Reward so the reward definition can change without
    changing historical award records.
    """

    __tablename__ = "player_rewards"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id"),
        nullable=False,
        index=True,
    )

    reward_id: Mapped[int] = mapped_column(
        ForeignKey("rewards.id"),
        nullable=False,
        index=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
    )

    granted_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    fulfilled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    fulfilled_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    player: Mapped["Player"] = relationship(
        "Player",
        back_populates="rewards",
    )

    reward: Mapped["Reward"] = relationship(
        "Reward",
    )


# ============================================================================
# CHALLENGES
# ============================================================================


class Challenge(Base, TimestampMixin):
    """
    Time-bound activity.

    A challenge can be scheduled for a Friday/Saturday window or any other
    configurable period.

    The actual game implementation is represented by game_type/config rather
    than hard-coding "draw a circle".
    """

    __tablename__ = "challenges"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    phase_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("phases.id"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    game_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="generic",
    )

    # JSON string for game-specific configuration.
    # Example:
    # {"attempts_required":5,"elite_percentile":90}
    config_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    start_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    end_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    participation_xp: Mapped[int] = mapped_column(
        Integer,
        default=300,
        nullable=False,
    )

    elite_xp: Mapped[int] = mapped_column(
        Integer,
        default=1500,
        nullable=False,
    )

    winner_xp: Mapped[int] = mapped_column(
        Integer,
        default=3000,
        nullable=False,
    )

    group_xp: Mapped[int] = mapped_column(
        Integer,
        default=5000,
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    phase: Mapped[Optional["Phase"]] = relationship(
        "Phase",
        back_populates="challenges",
    )

    attempts: Mapped[list["ChallengeAttempt"]] = relationship(
        "ChallengeAttempt",
        back_populates="challenge",
        cascade="all, delete-orphan",
    )


class ChallengeAttempt(Base):
    """
    Evidence/result for a challenge attempt.

    We do not trust the browser to tell us that a player was the winner.

    The backend records:
    - player;
    - challenge;
    - score;
    - attempt count;
    - timestamps;
    - verification status.

    The challenge service determines rankings server-side.
    """

    __tablename__ = "challenge_attempts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    challenge_id: Mapped[int] = mapped_column(
        ForeignKey("challenges.id"),
        nullable=False,
        index=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id"),
        nullable=False,
        index=True,
    )

    attempt_number: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    score: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    performance_percentile: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    submitted_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    participation_awarded: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    elite_awarded: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    winner_awarded: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    # Optional client evidence reference.
    evidence_hash: Mapped[Optional[str]] = mapped_column(
        String(128),
        nullable=True,
    )

    # ------------------------------------------------------------------
    # Challenge workflow state
    # ------------------------------------------------------------------

    attempt_reference: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="created",
        nullable=False,
        index=True,
    )

    evidence_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
    )

    evidence_payload: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    rejection_reason: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    verified_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    percentile: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
    )

    elite: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    winner: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    participation_xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    elite_xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    winner_xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    individual_xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    group_xp: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    challenge: Mapped["Challenge"] = relationship(
        "Challenge",
        back_populates="attempts",
    )

    player: Mapped["Player"] = relationship(
        "Player",
        back_populates="challenge_attempts",
    )


# ============================================================================
# COMMUNITY AWARDS
# ============================================================================


class CommunityAward(Base, TimestampMixin):
    """
    Public/community nomination.

    Submitted-by fields are staff-only.

    A public form should NEVER expose:
        submitted_by_name
        submitted_by_contact

    to players.
    """

    __tablename__ = "community_awards"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    player_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("players.id"),
        nullable=True,
        index=True,
    )

    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("groups.id"),
        nullable=True,
        index=True,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # ------------------------------------------------------------------
    # Submitter information.
    #
    # These are deliberately isolated to this staff-only record.
    # ------------------------------------------------------------------

    submitted_by_name: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )

    submitted_by_organisation: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )

    submitted_by_contact: Mapped[Optional[str]] = mapped_column(
        String(300),
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="pending",
        nullable=False,
        index=True,
    )

    xp: Mapped[int] = mapped_column(
        Integer,
        default=5000,
        nullable=False,
    )

    reviewed_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    player: Mapped[Optional["Player"]] = relationship(
        "Player",
        back_populates="community_awards",
    )


# ============================================================================
# KUDOS / POSITIVE REACTIONS
# ============================================================================


class Kudos(Base):
    """
    Fixed positive reaction.

    There is intentionally no free-text social messaging.

    Examples:
        awesome
        helpful
        brave
        team_player
        inspiring

    A player can only give the same reaction to the same recipient once
    per configured period/session.
    """

    __tablename__ = "kudos"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    giver_player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id"),
        nullable=False,
        index=True,
    )

    recipient_player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id"),
        nullable=False,
        index=True,
    )

    reaction_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    giver: Mapped["Player"] = relationship(
        "Player",
        foreign_keys=[giver_player_id],
    )

    recipient: Mapped["Player"] = relationship(
        "Player",
        foreign_keys=[recipient_player_id],
        back_populates="kudos_received",
    )

    __table_args__ = (
        CheckConstraint(
            "giver_player_id != recipient_player_id",
            name="ck_kudos_not_self",
        ),
        Index(
            "ix_kudos_recipient_created",
            "recipient_player_id",
            "created_at",
        ),
    )


# ============================================================================
# RESOURCES
# ============================================================================


class Resource(Base, TimestampMixin):
    """
    Resource library item.

    Resources can be associated with a phase so that relevant material
    becomes available without overwhelming players with everything at once.
    """

    __tablename__ = "resources"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    phase_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("phases.id"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    resource_type: Mapped[str] = mapped_column(
        String(50),
        default="link",
        nullable=False,
    )

    url: Mapped[Optional[str]] = mapped_column(
        String(2000),
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    phase: Mapped[Optional["Phase"]] = relationship(
        "Phase",
        back_populates="resources",
    )


# ============================================================================
# NOTIFICATIONS
# ============================================================================


class Notification(Base, TimestampMixin):
    """
    In-app notification.

    This is separate from actual browser push delivery.

    A notification can be created for:
    - one player;
    - all players;
    - a group;
    - staff.

    Push delivery is handled by the notification service.
    """

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    player_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("players.id"),
        nullable=True,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    body: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    notification_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="general",
    )

    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )


class PushSubscription(Base, TimestampMixin):
    """
    Browser push subscription.

    The platform can support browser notifications without requiring a
    native iOS/Android application.

    A player may have multiple devices.
    """

    __tablename__ = "push_subscriptions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id"),
        nullable=False,
        index=True,
    )

    endpoint: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    p256dh: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    auth: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    last_used_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "player_id",
            "endpoint",
            name="uq_push_player_endpoint",
        ),
    )


# ============================================================================
# FLASH EVENTS
# ============================================================================


class FlashEvent(Base, TimestampMixin):
    """
    A scheduled/randomised intervention window.

    This is distinct from Challenge because the event controls delivery
    behaviour, notifications and timing while one or more challenges can
    be associated with it later.
    """

    __tablename__ = "flash_events"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        index=True,
    )

    duration_seconds: Mapped[int] = mapped_column(
        Integer,
        default=300,
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    notification_title: Mapped[Optional[str]] = mapped_column(
        String(200),
        nullable=True,
    )

    notification_body: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )


# ============================================================================
# COMMUNITY / QR TOKENS
# ============================================================================


class CommunityAwardToken(Base, TimestampMixin):
    """
    Short-lived token used for community QR awards.

    IMPORTANT:

    The QR code should NOT contain the player's identity directly.

    Instead it contains an opaque token which resolves server-side to:
        programme
        optional player
        optional group
        expiry
        usage limits

    This allows us to rotate/revoke tokens and prevents people constructing
    URLs such as /award?player_id=123.
    """

    __tablename__ = "community_award_tokens"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    player_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("players.id"),
        nullable=True,
        index=True,
    )

    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("groups.id"),
        nullable=True,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(128),
        unique=True,
        nullable=False,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
    )

    max_uses: Mapped[int] = mapped_column(
        Integer,
        default=1,
        nullable=False,
    )

    use_count: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )


# ============================================================================
# CODE OF CONDUCT
# ============================================================================


class ConductRule(Base, TimestampMixin):
    """
    Configurable behavioural rule.

    Young people can help define the language/content of these rules,
    while the staff dashboard controls their operational use.
    """

    __tablename__ = "conduct_rules"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    tier: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    xp_penalty: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    restorative_required: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "tier >= 1 AND tier <= 3",
            name="ck_conduct_rule_tier",
        ),
    )


class ConductIncident(Base, TimestampMixin):
    """
    Staff-recorded behavioural incident.

    This is separate from XPTransaction because an incident contains the
    contextual information needed for safeguarding/restorative work.

    The XP service creates the actual ledger transaction if a penalty
    is approved.
    """

    __tablename__ = "conduct_incidents"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id"),
        nullable=False,
        index=True,
    )

    conduct_rule_id: Mapped[int] = mapped_column(
        ForeignKey("conduct_rules.id"),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="open",
        nullable=False,
    )

    restorative_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    points_reinstated: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    recorded_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )


# ============================================================================
# EXCEPTIONAL GROUP PENALTIES
# ============================================================================


class GroupPenalty(Base, TimestampMixin):
    """
    Explicit record for the exceptional group-point-loss protocol.

    This prevents ordinary individual behaviour from accidentally reducing
    the collective pool.

    A service layer must enforce:
        - collective criteria;
        - maximum programme penalty percentage;
        - staff authorisation;
        - audit record;
        - restorative action.
    """

    __tablename__ = "group_penalties"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    group_id: Mapped[int] = mapped_column(
        ForeignKey("groups.id"),
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    collective_complicity: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    severe_shared_impact: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    passive_group_endorsement: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    approved_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    restorative_completed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "amount > 0",
            name="ck_group_penalty_positive_amount",
        ),
    )


# ============================================================================
# ADMIN / SYSTEM SETTINGS
# ============================================================================


class SystemSetting(Base, TimestampMixin):
    """
    Generic programme configuration.

    Use typed first-class columns for important business rules.

    This table is for secondary configurable settings such as:
        leaderboard refresh interval
        public leaderboard enabled
        notifications enabled
        flash-event notifications enabled
        player kudos enabled
    """

    __tablename__ = "system_settings"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    key: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    value: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    value_type: Mapped[str] = mapped_column(
        String(30),
        default="string",
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    editable_by_staff: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            "programme_id",
            "key",
            name="uq_programme_setting_key",
        ),
    )


# ============================================================================
# ADMIN AUDIT LOG
# ============================================================================


class PointAwardRequest(Base, TimestampMixin):
    """Extra-XP request submitted through a player's personal Quest QR."""

    __tablename__ = "point_award_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    requested_xp: Mapped[int] = mapped_column(Integer, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True
    )
    reviewed_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True, index=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True
    )
    review_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    player: Mapped["Player"] = relationship("Player")
    reviewer: Mapped[Optional["User"]] = relationship(
        "User", foreign_keys=[reviewed_by]
    )


class AuditLog(Base):
    """
    Security/audit trail.

    Every meaningful administrative action should be recorded here.

    Examples:
        player.suspended
        player.reactivated
        player.gamertag.changed
        xp.awarded
        xp.penalised
        group_penalty.created
        reward.fulfilled
        programme.theme.changed
        programme.map.changed
        phase.activated
        account.disabled
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    action: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        index=True,
    )

    entity_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    entity_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        nullable=True,
    )

    details: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    ip_address: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
    )

    user_agent: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    user: Mapped[Optional["User"]] = relationship(
        "User",
        back_populates="audit_logs",
    )


# ============================================================================
# SAFEGUARDING / FLAGGING
# ============================================================================


class EngagementFlag(Base, TimestampMixin):
    """
    Internal staff-only signal.

    This is NOT a public/player-facing reputation score.

    Examples:
        repeated_absence
        declining_engagement
        challenge_dropoff
        staff_follow_up_required

    The system should assist staff, not automatically label young people.
    """

    __tablename__ = "engagement_flags"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    player_id: Mapped[int] = mapped_column(
        ForeignKey("players.id"),
        nullable=False,
        index=True,
    )

    flag_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    severity: Mapped[str] = mapped_column(
        String(30),
        default="info",
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        default="open",
        nullable=False,
    )

    resolved_by: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
    )

    resolved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )


# ============================================================================
# GAME CONFIGURATION
# ============================================================================


class GameDefinition(Base, TimestampMixin):
    """
    Registry of supported mini-game types.

    The actual frontend game implementations are known by code, but the
    programme chooses which ones are active/configured through this table.

    Examples:
        reaction
        draw_accuracy
        memory
        timing
        pattern
        rapid_decision
    """

    __tablename__ = "game_definitions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    description: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )


class ProgrammeGame(Base, TimestampMixin):
    """
    Enables/configures a game for a programme.
    """

    __tablename__ = "programme_games"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    game_id: Mapped[int] = mapped_column(
        ForeignKey("game_definitions.id"),
        nullable=False,
        index=True,
    )

    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    config_json: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            "programme_id",
            "game_id",
            name="uq_programme_game",
        ),
    )


# ============================================================================
# GLOBAL PROGRAMME MILESTONES
# ============================================================================


class ProgrammeMilestone(Base, TimestampMixin):
    """
    Collective jackpot milestones.

    These replace hard-coded assumptions such as:
        500,000 -> £250
        1,000,000 -> £750
        1,500,000 -> £2,200
    """

    __tablename__ = "programme_milestones"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    xp_threshold: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    reward_description: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
    )

    reward_value: Mapped[float] = mapped_column(
        Float,
        default=0,
        nullable=False,
    )

    reward_type: Mapped[str] = mapped_column(
        String(50),
        default="group",
        nullable=False,
    )

    sort_order: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )

    active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    awarded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        nullable=True,
    )


# ============================================================================
# OPTIONAL: STAFF-ISSUED MANUAL POINT AWARDS
# ============================================================================


class ManualAward(Base, TimestampMixin):
    """
    Explicit staff-created award.

    This gives youth workers a controlled mechanism for exceptional positive
    behaviour without having to create a fake challenge or community award.
    """

    __tablename__ = "manual_awards"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    programme_id: Mapped[int] = mapped_column(
        ForeignKey("programmes.id"),
        nullable=False,
        index=True,
    )

    player_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("players.id"),
        nullable=True,
        index=True,
    )

    group_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("groups.id"),
        nullable=True,
        index=True,
    )

    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    approved_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    xp_transaction_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("xp_transactions.id"),
        nullable=True,
    )


# ============================================================================
# DATABASE INDEXES
# ============================================================================

Index(
    "ix_xp_transactions_programme_created",
    XPTransaction.programme_id,
    XPTransaction.created_at,
)

Index(
    "ix_xp_transactions_player_created",
    XPTransaction.player_id,
    XPTransaction.created_at,
)

Index(
    "ix_xp_transactions_group_created",
    XPTransaction.group_id,
    XPTransaction.created_at,
)

Index(
    "ix_challenge_attempts_challenge_score",
    ChallengeAttempt.challenge_id,
    ChallengeAttempt.score,
)

Index(
    "ix_players_group_active",
    Player.group_id,
    Player.active,
)

Index(
    "ix_players_public_visibility",
    Player.public_visible,
    Player.active,
)

Index(
    "ix_community_awards_status_created",
    CommunityAward.status,
    CommunityAward.created_at,
)

Index(
    "ix_engagement_flags_player_status",
    EngagementFlag.player_id,
    EngagementFlag.status,
)
