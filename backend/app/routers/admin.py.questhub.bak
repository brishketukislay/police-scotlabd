from datetime import date

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db.database import get_db

from ..db.models import (
    User,
    Player,
    YouthGroup,
    Programme,
    Theme,
    GameMap,
    MapLocation,
    Phase,
    PhaseLocation,
    PointRule,
    Reward,
    ProgrammeMilestone,
    AuditLog,
    CommunityAward,
    SkillTree,
    SkillMilestone,
)

from ..auth import (
    require_roles,
    hash_password,
)

from ..services.xp import (
    award_xp,
    player_xp,
    group_xp,
)

from ..services.gamification import (
    award_individual_penalty,
)

from ..services.xp import (
    award_positive_xp,
    programme_xp,
)


router = APIRouter(
    prefix="/api/admin",
    tags=["admin"],
)


# ============================================================
# HELPERS
# ============================================================

def get_programme(
    db: Session,
) -> Programme:
    programme = (
        db.query(Programme)
        .filter(
            Programme.active == True
        )
        .first()
    )

    if not programme:
        raise HTTPException(
            status_code=404,
            detail="No active programme configured",
        )

    return programme


def audit(
    db: Session,
    user_id: int,
    action: str,
    details: str,
):
    db.add(
        AuditLog(
            user_id=user_id,
            action=action,
            details=details,
        )
    )


# ============================================================
# AUDIT LOG
# ============================================================

@router.get("/audit")
def get_audit_logs(
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
    limit: int = 50,
    offset: int = 0,
):
    limit = max(1, min(limit, 100))
    offset = max(0, offset)

    total = (
        db.query(AuditLog)
        .count()
    )

    logs = (
        db.query(AuditLog)
        .order_by(
            AuditLog.created_at.desc(),
            AuditLog.id.desc(),
        )
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "items": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at,
                "username": (
                    log.user.username
                    if log.user
                    else None
                ),
            }
            for log in logs
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ============================================================
# OVERVIEW
# ============================================================

@router.get("/overview")
def overview(
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    players = (
        db.query(Player)
        .filter(Player.active == True)
        .all()
    )

    current_xp = group_xp(
        db,
        programme.id,
    )

    target_xp = programme.target_xp or 0

    progress_percent = (
        (current_xp / target_xp) * 100
        if target_xp > 0
        else 0
    )

    return {
        "players": len(players),
        "staff": db.query(User)
        .filter(
            User.role.in_(
                [
                    "admin",
                    "youth_worker",
                ]
            )
        )
        .count(),
        "group_xp": current_xp,
        "target_xp": target_xp,
        "progress_percent": round(
            progress_percent,
            2,
        ),
        "weekly_target_xp": (
            programme.weekly_target_xp
            or 0
        ),
        "programme": programme.name,
    }


# ============================================================
# ADMIN AUDIT LOG
# ============================================================

@router.get("/audit-logs")
def get_audit_logs(
    limit: int = 100,
    offset: int = 0,
    action: str | None = None,
    user_id: int | None = None,
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    """
    Return the most recent administrative audit events.

    Audit logs are staff-only and read-only. Existing audit
    writers remain authoritative for creating entries.
    """

    limit = max(1, min(limit, 250))
    offset = max(0, offset)

    query = db.query(AuditLog)

    if action:
        query = query.filter(
            AuditLog.action == action.strip()
        )

    if user_id is not None:
        query = query.filter(
            AuditLog.user_id == user_id
        )

    total = query.count()

    logs = (
        query
        .order_by(AuditLog.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return {
        "items": [
            {
                "id": log.id,
                "user_id": log.user_id,
                "action": log.action,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "details": log.details,
                "ip_address": log.ip_address,
                "user_agent": log.user_agent,
                "created_at": log.created_at,
                "username": (
                    log.user.username
                    if log.user
                    else None
                ),
            }
            for log in logs
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


# ============================================================
# PROGRAMME CONFIGURATION
# ============================================================

class ProgrammeSettingsRequest(BaseModel):
    name: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    target_xp: int | None = None
    group_name: str | None = None
    active: bool | None = None


class PhaseRequest(BaseModel):
    name: str
    description: str | None = None
    colour: str | None = None
    icon: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    active: bool | None = True


class ProgrammeRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=5000,
    )

    start_date: date | None = None
    end_date: date | None = None

    target_xp: int = Field(
        default=1_500_000,
        ge=1,
        le=100_000_000,
    )

    weekly_target_xp: int | None = Field(
        default=None,
        ge=0,
        le=10_000_000,
    )

    max_group_penalty_percent: float = Field(
        default=10.0,
        ge=0,
        le=100,
    )


@router.get("/programme")
def get_programme_configuration(
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    return {
        "id": programme.id,
        "name": programme.name,
        "description": programme.description,
        "start_date": programme.start_date,
        "end_date": programme.end_date,
        "target_xp": programme.target_xp,
        "weekly_target_xp": (
            programme.weekly_target_xp
        ),
        "max_group_penalty_percent": (
            programme.max_group_penalty_percent
        ),
        "active_theme_id": (
            programme.active_theme_id
        ),
        "active_map_id": (
            programme.active_map_id
        ),
        "active_phase_id": (
            programme.active_phase_id
        ),
    }


@router.put("/programme")
def update_programme_configuration(
    data: ProgrammeRequest,
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    if (
        data.end_date is not None
        and data.start_date is not None
        and data.end_date < data.start_date
    ):
        raise HTTPException(
            status_code=400,
            detail="End date cannot be before start date.",
        )

    old_values = (
        f"name={programme.name};"
        f"target_xp={programme.target_xp};"
        f"weekly_target_xp="
        f"{programme.weekly_target_xp};"
        f"max_group_penalty_percent="
        f"{programme.max_group_penalty_percent}"
    )

    programme.name = data.name.strip()
    programme.description = (
        data.description.strip()
        if data.description
        else None
    )
    programme.start_date = data.start_date
    programme.end_date = data.end_date
    programme.target_xp = data.target_xp
    programme.weekly_target_xp = (
        data.weekly_target_xp
    )
    programme.max_group_penalty_percent = (
        data.max_group_penalty_percent
    )

    audit(
        db,
        user.id,
        "programme.updated",
        (
            f"old=[{old_values}];"
            f"new=["
            f"name={programme.name};"
            f"target_xp={programme.target_xp};"
            f"weekly_target_xp="
            f"{programme.weekly_target_xp};"
            f"max_group_penalty_percent="
            f"{programme.max_group_penalty_percent}"
            f"]"
        ),
    )

    db.commit()

    return {
        "success": True,
        "id": programme.id,
    }


# ============================================================
# STAFF XP AWARDS
# ============================================================

class StaffAwardXPRequest(BaseModel):
    player_id: int

    amount: int = Field(
        ...,
        ge=-50_000,
        le=50_000,
    )

    reason: str = Field(
        ...,
        min_length=3,
        max_length=500,
    )


@router.post("/xp/award")
def award_player_xp(
    data: StaffAwardXPRequest,
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    player = (
        db.query(Player)
        .filter(
            Player.id == data.player_id,
            Player.active == True,
        )
        .first()
    )

    if not player:
        raise HTTPException(
            status_code=404,
            detail="Player not found.",
        )

    try:
        transaction = award_xp(
            db,
            programme_id=get_programme(db).id,
            player_id=player.id,
            amount=data.amount,
            group_amount=0,
            transaction_type=(
                "admin_adjustment"
            ),
            reason=data.reason,
            created_by=user.id,
        )

        db.commit()

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    audit(
        db,
        user.id,
        "xp.admin_adjustment",
        (
            f"player_id={player.id};"
            f"amount={data.amount};"
            f"reason={data.reason}"
        ),
    )

    db.commit()

    return {
        "success": True,
        "transaction_id": transaction.id,
    }






class PhaseResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    colour: str | None = None
    icon: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    active: bool
    programme_id: int


@router.get("/phases")
def get_phases(
    user=Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    phases = (
        db.query(Phase)
        .filter(
            Phase.programme_id == programme.id,
        )
        .order_by(
            Phase.start_date.asc(),
            Phase.id.asc(),
        )
        .all()
    )

    return [
        {
            "id": phase.id,
            "name": phase.name,
            "description": phase.description,
            "colour": phase.colour,
            "icon": phase.icon,
            "start_date": phase.start_date,
            "end_date": phase.end_date,
            "active": phase.active,
            "programme_id": phase.programme_id,
        }
        for phase in phases
    ]


@router.post("/phases")
def create_phase(
    data: PhaseRequest,
    user=Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    name = data.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Phase name is required.",
        )

    if (
        data.start_date is not None
        and data.end_date is not None
        and data.end_date < data.start_date
    ):
        raise HTTPException(
            status_code=400,
            detail="Phase end date cannot be before start date.",
        )

    phase = Phase(
        programme_id=programme.id,
        name=name,
        description=(
            data.description.strip()
            if data.description
            else None
        ),
        colour=(
            data.colour.strip()
            if data.colour
            else None
        ),
        icon=(
            data.icon.strip()
            if data.icon
            else "★"
        ),
        start_date=data.start_date,
        end_date=data.end_date,
        active=False,
    )

    db.add(phase)
    db.flush()

    audit(
        db,
        user.id,
        "phase.created",
        (
            f"phase_id={phase.id};"
            f"name={phase.name}"
        ),
    )

    db.commit()

    return {
        "success": True,
        "id": phase.id,
        "name": phase.name,
    }


@router.put("/phases/{phase_id}")
def update_phase(
    phase_id: int,
    data: PhaseRequest,
    user=Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    phase = (
        db.query(Phase)
        .filter(
            Phase.id == phase_id,
            Phase.programme_id == programme.id,
        )
        .first()
    )

    if not phase:
        raise HTTPException(
            status_code=404,
            detail="Phase not found.",
        )

    if (
        data.start_date is not None
        and data.end_date is not None
        and data.end_date < data.start_date
    ):
        raise HTTPException(
            status_code=400,
            detail="Phase end date cannot be before start date.",
        )

    phase.name = data.name.strip()
    phase.description = (
        data.description.strip()
        if data.description
        else None
    )

    if data.colour is not None:
        phase.colour = data.colour.strip()

    if data.icon is not None:
        phase.icon = data.icon.strip() or "★"

    phase.start_date = data.start_date
    phase.end_date = data.end_date

    if data.active is not None:
        phase.active = data.active

    audit(
        db,
        user.id,
        "phase.updated",
        (
            f"phase_id={phase.id};"
            f"name={phase.name};"
            f"active={phase.active}"
        ),
    )

    db.commit()

    return {
        "success": True,
        "id": phase.id,
    }


@router.delete("/phases/{phase_id}")
def delete_phase(
    phase_id: int,
    user=Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    phase = (
        db.query(Phase)
        .filter(
            Phase.id == phase_id,
            Phase.programme_id == programme.id,
        )
        .first()
    )

    if not phase:
        raise HTTPException(
            status_code=404,
            detail="Phase not found.",
        )

    if phase.active:
        raise HTTPException(
            status_code=400,
            detail="Active phase cannot be deleted. Activate another phase first.",
        )

    phase_name = phase.name

    db.delete(phase)

    audit(
        db,
        user.id,
        "phase.deleted",
        (
            f"phase_id={phase_id};"
            f"name={phase_name}"
        ),
    )

    db.commit()

    return {
        "success": True,
        "id": phase_id,
    }


@router.post("/phases/{phase_id}/activate")
def activate_phase(
    phase_id: int,
    user=Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    phase = (
        db.query(Phase)
        .filter(
            Phase.id == phase_id,
            Phase.programme_id == programme.id,
        )
        .first()
    )

    if not phase:
        raise HTTPException(
            status_code=404,
            detail="Phase not found.",
        )

    db.query(Phase).filter(
        Phase.programme_id == programme.id,
    ).update(
        {
            Phase.active: False,
        },
        synchronize_session=False,
    )

    phase.active = True

    programme.active_phase_id = phase.id

    audit(
        db,
        user.id,
        "phase.activated",
        (
            f"phase_id={phase.id};"
            f"name={phase.name}"
        ),
    )

    db.commit()

    return {
        "success": True,
        "id": phase.id,
    }


# ============================================================
# POINT ECONOMY
# ============================================================

class PointRuleRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    code: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    description: str | None = Field(
        default=None,
        max_length=1000,
    )

    individual_xp: int = Field(
        default=0,
        ge=0,
        le=1_000_000,
    )

    group_xp: int = Field(
        default=0,
        ge=0,
        le=1_000_000,
    )

    weekly_cap: int | None = Field(
        default=None,
        ge=0,
        le=10_000_000,
    )

    awards_per_week: float = Field(
        default=0,
        ge=0,
        le=100_000,
    )

    individual_award_cap: int | None = Field(
        default=None,
        ge=1,
        le=1_000_000,
    )

    group_award_cap: int | None = Field(
        default=None,
        ge=1,
        le=1_000_000,
    )

    enabled: bool = True


@router.get("/point-rules")
def get_point_rules(
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    rules = (
        db.query(PointRule)
        .filter(
            PointRule.programme_id
            == programme.id
        )
        .order_by(
            PointRule.name.asc()
        )
        .all()
    )

    return [
        {
            "id": rule.id,
            "name": rule.name,
            "code": rule.code,
            "description": rule.description,
            "individual_xp": (
                rule.individual_xp
            ),
            "group_xp": rule.group_xp,
            "weekly_cap": rule.weekly_cap,
            "awards_per_week": (
                rule.awards_per_week
            ),
            "individual_award_cap": (
                rule.individual_award_cap
            ),
            "group_award_cap": (
                rule.group_award_cap
            ),
            "enabled": rule.enabled,
        }
        for rule in rules
    ]


@router.post("/point-rules")
def create_point_rule(
    data: PointRuleRequest,
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    code = data.code.strip().lower()

    existing = (
        db.query(PointRule)
        .filter(
            PointRule.programme_id
            == programme.id,
            PointRule.code == code,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                "A point rule with this code "
                "already exists."
            ),
        )

    if (
        data.individual_xp == 0
        and data.group_xp == 0
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "A point rule must award "
                "some XP."
            ),
        )

    rule = PointRule(
        programme_id=programme.id,
        name=data.name.strip(),
        code=code,
        description=(
            data.description.strip()
            if data.description
            else None
        ),
        individual_xp=data.individual_xp,
        group_xp=data.group_xp,
        weekly_cap=data.weekly_cap,
        awards_per_week=(
            data.awards_per_week
        ),
        individual_award_cap=(
            data.individual_award_cap
        ),
        group_award_cap=(
            data.group_award_cap
        ),
        enabled=data.enabled,
    )

    db.add(rule)

    db.flush()

    audit(
        db,
        user.id,
        "point_rule.created",
        (
            f"id={rule.id};"
            f"code={code};"
            f"individual_xp="
            f"{data.individual_xp};"
            f"group_xp="
            f"{data.group_xp}"
        ),
    )

    db.commit()

    return {
        "success": True,
        "id": rule.id,
    }


@router.put("/point-rules/{rule_id}")
def update_point_rule(
    rule_id: int,
    data: PointRuleRequest,
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    rule = (
        db.query(PointRule)
        .filter(
            PointRule.id == rule_id,
            PointRule.programme_id
            == programme.id,
        )
        .first()
    )

    if not rule:
        raise HTTPException(
            status_code=404,
            detail="Point rule not found.",
        )

    code = data.code.strip().lower()

    duplicate = (
        db.query(PointRule)
        .filter(
            PointRule.programme_id
            == programme.id,
            PointRule.code == code,
            PointRule.id != rule.id,
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail=(
                "A point rule with this code "
                "already exists."
            ),
        )

    if (
        data.individual_xp == 0
        and data.group_xp == 0
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                "A point rule must award "
                "some XP."
            ),
        )

    old_values = (
        f"name={rule.name};"
        f"code={rule.code};"
        f"individual_xp="
        f"{rule.individual_xp};"
        f"group_xp={rule.group_xp};"
        f"weekly_cap="
        f"{rule.weekly_cap};"
        f"awards_per_week="
        f"{rule.awards_per_week};"
        f"individual_award_cap="
        f"{rule.individual_award_cap};"
        f"group_award_cap="
        f"{rule.group_award_cap};"
        f"enabled={rule.enabled}"
    )

    rule.name = data.name.strip()
    rule.code = code
    rule.description = (
        data.description.strip()
        if data.description
        else None
    )
    rule.individual_xp = (
        data.individual_xp
    )
    rule.group_xp = data.group_xp
    rule.weekly_cap = data.weekly_cap
    rule.awards_per_week = (
        data.awards_per_week
    )
    rule.individual_award_cap = (
        data.individual_award_cap
    )
    rule.group_award_cap = (
        data.group_award_cap
    )
    rule.enabled = data.enabled

    audit(
        db,
        user.id,
        "point_rule.updated",
        (
            f"id={rule.id};"
            f"old=[{old_values}];"
            f"new=["
            f"name={rule.name};"
            f"code={rule.code};"
            f"individual_xp="
            f"{rule.individual_xp};"
            f"group_xp={rule.group_xp};"
            f"weekly_cap="
            f"{rule.weekly_cap};"
            f"awards_per_week="
            f"{rule.awards_per_week};"
            f"individual_award_cap="
            f"{rule.individual_award_cap};"
            f"group_award_cap="
            f"{rule.group_award_cap};"
            f"enabled={rule.enabled}"
            f"]"
        ),
    )

    db.commit()

    return {
        "success": True,
        "id": rule.id,
    }


@router.delete("/point-rules/{rule_id}")
def disable_point_rule(
    rule_id: int,
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    rule = (
        db.query(PointRule)
        .filter(
            PointRule.id == rule_id,
            PointRule.programme_id
            == programme.id,
        )
        .first()
    )

    if not rule:
        raise HTTPException(
            status_code=404,
            detail="Point rule not found.",
        )

    rule.enabled = False

    audit(
        db,
        user.id,
        "point_rule.disabled",
        (
            f"id={rule.id};"
            f"code={rule.code}"
        ),
    )

    db.commit()

    return {
        "success": True,
        "id": rule.id,
        "enabled": False,
    }


# ============================================================
# REWARDS
# ============================================================

class RewardRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    xp_threshold: int | None = Field(
        default=None,
        ge=0,
        le=1_000_000,
    )

    reward_type: str = Field(
        default="physical",
        min_length=2,
        max_length=100,
    )

    value: float = Field(
        default=0,
        ge=0,
        le=1_000_000,
    )

    active: bool = True


def reward_response(reward: Reward):
    return {
        "id": reward.id,
        "programme_id": reward.programme_id,
        "name": reward.name,
        "description": reward.description,
        "xp_threshold": reward.xp_threshold,
        "reward_type": reward.reward_type,
        "value": reward.value,
        "currency": reward.currency,
        "badge_id": reward.badge_id,
        "mystery": reward.mystery,
        "active": reward.active,
    }


@router.get("/rewards")
def get_rewards(
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    rewards = (
        db.query(Reward)
        .filter(
            Reward.programme_id == programme.id
        )
        .order_by(
            Reward.xp_threshold.asc(),
            Reward.id.asc(),
        )
        .all()
    )

    return [
        reward_response(reward)
        for reward in rewards
    ]


@router.post("/rewards")
def create_reward(
    data: RewardRequest,
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    reward = Reward(
        programme_id=programme.id,
        name=data.name.strip(),
        description=(
            data.description.strip()
            if data.description
            else None
        ),
        xp_threshold=data.xp_threshold,
        reward_type=data.reward_type.strip(),
        value=data.value,
        currency="GBP",
        active=data.active,
    )

    db.add(reward)
    db.flush()

    audit(
        db,
        user.id,
        "reward.created",
        (
            f"id={reward.id};"
            f"programme_id={programme.id};"
            f"name={reward.name};"
            f"xp_threshold={reward.xp_threshold};"
            f"reward_type={reward.reward_type};"
            f"value={reward.value};"
            f"active={reward.active}"
        ),
    )

    db.commit()

    return {
        "success": True,
        "id": reward.id,
    }


@router.put("/rewards/{reward_id}")
def update_reward(
    reward_id: int,
    data: RewardRequest,
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    reward = (
        db.query(Reward)
        .filter(
            Reward.id == reward_id,
            Reward.programme_id == programme.id,
        )
        .first()
    )

    if not reward:
        raise HTTPException(
            status_code=404,
            detail="Reward not found.",
        )

    reward.name = data.name.strip()

    reward.description = (
        data.description.strip()
        if data.description
        else None
    )

    reward.xp_threshold = data.xp_threshold
    reward.reward_type = data.reward_type.strip()
    reward.value = data.value
    reward.active = data.active

    audit(
        db,
        user.id,
        "reward.updated",
        (
            f"id={reward.id};"
            f"programme_id={programme.id};"
            f"name={reward.name};"
            f"xp_threshold={reward.xp_threshold};"
            f"reward_type={reward.reward_type};"
            f"value={reward.value};"
            f"active={reward.active}"
        ),
    )

    db.commit()

    return {
        "success": True,
        "id": reward.id,
    }


@router.delete("/rewards/{reward_id}")
def disable_reward(
    reward_id: int,
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    reward = (
        db.query(Reward)
        .filter(
            Reward.id == reward_id,
            Reward.programme_id == programme.id,
        )
        .first()
    )

    if not reward:
        raise HTTPException(
            status_code=404,
            detail="Reward not found.",
        )

    reward.active = False

    audit(
        db,
        user.id,
        "reward.disabled",
        (
            f"id={reward.id};"
            f"programme_id={programme.id};"
            f"name={reward.name}"
        ),
    )

    db.commit()

    return {
        "success": True,
        "id": reward.id,
    }


# JACKPOT / PROGRAMME MILESTONES
# ============================================================

class ProgrammeMilestoneRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    xp_threshold: int = Field(
        ...,
        ge=1,
        le=100_000_000,
    )

    reward_description: str | None = Field(
        default=None,
        max_length=500,
    )

    reward_value: float = Field(
        default=0,
        ge=0,
        le=1_000_000,
    )

    reward_type: str = Field(
        default="group",
        min_length=2,
        max_length=50,
    )

    sort_order: int = Field(
        default=0,
        ge=0,
        le=1000,
    )

    active: bool = True


def milestone_response(
    milestone: ProgrammeMilestone,
    current_xp: int,
):
    threshold = (
        milestone.xp_threshold
    )

    achieved = (
        current_xp >= threshold
    )

    return {
        "id": milestone.id,
        "name": milestone.name,
        "xp_threshold": threshold,
        "reward_description": (
            milestone.reward_description
        ),
        "reward_value": (
            milestone.reward_value
        ),
        "reward_type": (
            milestone.reward_type
        ),
        "sort_order": (
            milestone.sort_order
        ),
        "active": milestone.active,
        "achieved": achieved,
        "awarded_at": (
            milestone.awarded_at
        ),
    }


@router.get("/jackpot")
def get_jackpot(
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    current_xp = group_xp(
        db,
        programme.id,
    )

    target_xp = (
        programme.target_xp or 0
    )

    progress_percent = (
        (current_xp / target_xp) * 100
        if target_xp > 0
        else 0
    )

    milestones = (
        db.query(ProgrammeMilestone)
        .filter(
            ProgrammeMilestone.programme_id
            == programme.id
        )
        .order_by(
            ProgrammeMilestone.sort_order.asc(),
            ProgrammeMilestone.xp_threshold.asc(),
            ProgrammeMilestone.id.asc(),
        )
        .all()
    )

    return {
        "programme": {
            "id": programme.id,
            "name": programme.name,
            "target_xp": target_xp,
            "weekly_target_xp": (
                programme.weekly_target_xp
                or 0
            ),
            "max_group_penalty_percent": (
                programme.max_group_penalty_percent
            ),
        },
        "current_xp": current_xp,
        "progress_percent": round(
            min(progress_percent, 100),
            2,
        ),
        "remaining_xp": max(
            target_xp - current_xp,
            0,
        ),
        "milestones": [
            milestone_response(
                milestone,
                current_xp,
            )
            for milestone in milestones
            if milestone.active
        ],
    }


@router.post("/jackpot/milestones")
def create_jackpot_milestone(
    data: ProgrammeMilestoneRequest,
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    existing = (
        db.query(ProgrammeMilestone)
        .filter(
            ProgrammeMilestone.programme_id
            == programme.id,
            ProgrammeMilestone.xp_threshold
            == data.xp_threshold,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=409,
            detail=(
                "A milestone already exists "
                "at this XP threshold."
            ),
        )

    milestone = ProgrammeMilestone(
        programme_id=programme.id,
        name=data.name.strip(),
        xp_threshold=data.xp_threshold,
        reward_description=(
            data.reward_description.strip()
            if data.reward_description
            else None
        ),
        reward_value=data.reward_value,
        reward_type=data.reward_type.strip(),
        sort_order=data.sort_order,
        active=data.active,
    )

    db.add(milestone)

    db.flush()

    audit(
        db,
        user.id,
        "programme_milestone.created",
        (
            f"id={milestone.id};"
            f"threshold="
            f"{milestone.xp_threshold};"
            f"reward="
            f"{milestone.reward_value}"
        ),
    )

    db.commit()

    return {
        "success": True,
        "id": milestone.id,
    }


@router.put(
    "/jackpot/milestones/{milestone_id}"
)
def update_jackpot_milestone(
    milestone_id: int,
    data: ProgrammeMilestoneRequest,
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    milestone = (
        db.query(ProgrammeMilestone)
        .filter(
            ProgrammeMilestone.id
            == milestone_id,
            ProgrammeMilestone.programme_id
            == programme.id,
        )
        .first()
    )

    if not milestone:
        raise HTTPException(
            status_code=404,
            detail="Milestone not found.",
        )

    duplicate = (
        db.query(ProgrammeMilestone)
        .filter(
            ProgrammeMilestone.programme_id
            == programme.id,
            ProgrammeMilestone.xp_threshold
            == data.xp_threshold,
            ProgrammeMilestone.id
            != milestone.id,
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail=(
                "Another milestone already "
                "uses this XP threshold."
            ),
        )

    old_values = (
        f"name={milestone.name};"
        f"threshold="
        f"{milestone.xp_threshold};"
        f"reward="
        f"{milestone.reward_value};"
        f"active={milestone.active}"
    )

    milestone.name = data.name.strip()
    milestone.xp_threshold = (
        data.xp_threshold
    )
    milestone.reward_description = (
        data.reward_description.strip()
        if data.reward_description
        else None
    )
    milestone.reward_value = (
        data.reward_value
    )
    milestone.reward_type = (
        data.reward_type.strip()
    )
    milestone.sort_order = (
        data.sort_order
    )
    milestone.active = data.active

    audit(
        db,
        user.id,
        "programme_milestone.updated",
        (
            f"id={milestone.id};"
            f"old=[{old_values}];"
            f"new=["
            f"name={milestone.name};"
            f"threshold="
            f"{milestone.xp_threshold};"
            f"reward="
            f"{milestone.reward_value};"
            f"active={milestone.active}"
            f"]"
        ),
    )

    db.commit()

    return {
        "success": True,
        "id": milestone.id,
    }


@router.delete(
    "/jackpot/milestones/{milestone_id}"
)
def disable_jackpot_milestone(
    milestone_id: int,
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    milestone = (
        db.query(ProgrammeMilestone)
        .filter(
            ProgrammeMilestone.id
            == milestone_id,
            ProgrammeMilestone.programme_id
            == programme.id,
        )
        .first()
    )

    if not milestone:
        raise HTTPException(
            status_code=404,
            detail="Milestone not found.",
        )

    milestone.active = False

    audit(
        db,
        user.id,
        "programme_milestone.disabled",
        (
            f"id={milestone.id};"
            f"name={milestone.name}"
        ),
    )

    db.commit()

    return {
        "success": True,
        "id": milestone.id,
        "active": False,
    }


# ============================================================
# THEMES
# ============================================================

class ThemeRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    primary: str = Field(
        default="#18775B",
        min_length=4,
        max_length=20,
    )

    secondary: str = Field(
        default="#0F513C",
        min_length=4,
        max_length=20,
    )

    accent: str = Field(
        default="#43B98B",
        min_length=4,
        max_length=20,
    )

    background: str = Field(
        default="#F3F7F5",
        min_length=4,
        max_length=20,
    )

    surface: str = Field(
        default="#FFFFFF",
        min_length=4,
        max_length=20,
    )

    text: str = Field(
        default="#17221E",
        min_length=4,
        max_length=20,
    )

    logo_url: str | None = Field(
        default=None,
        max_length=1000,
    )

    font_family: str | None = Field(
        default=None,
        max_length=100,
    )


def theme_response(
    theme: Theme,
    programme: Programme,
):
    return {
        "id": theme.id,
        "name": theme.name,
        "primary": theme.primary,
        "secondary": theme.secondary,
        "accent": theme.accent,
        "background": theme.background,
        "surface": theme.surface,
        "text": theme.text,
        "logo_url": theme.logo_url,
        "font_family": theme.font_family,
        "active": theme.active,
        "selected": (
            theme.id == programme.active_theme_id
        ),
    }


@router.get("/maps")
def admin_maps(
    user=Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    maps = (
        db.query(GameMap)
        .filter(GameMap.programme_id == programme.id)
        .order_by(GameMap.name.asc(), GameMap.id.asc())
        .all()
    )

    return [
        {
            "id": game_map.id,
            "name": game_map.name,
            "description": game_map.description,
            "background_image": game_map.background_image,
            "active": game_map.active,
            "locations": [
                {
                    "id": location.id,
                    "name": location.name,
                    "description": location.description,
                    "x": location.x,
                    "y": location.y,
                    "icon": location.icon,
                    "active": location.active,
                    "phases": [
                        {
                            "id": link.phase.id,
                            "name": link.phase.name,
                        }
                        for link in location.phase_links
                        if link.phase is not None
                    ],
                }
                for location in game_map.locations
            ],
        }
        for game_map in maps
    ]


class MapRequest(BaseModel):
    name: str
    description: str | None = None
    background_image: str | None = None
    active: bool = True


class MapLocationRequest(BaseModel):
    name: str
    description: str | None = None
    x: float = 0.5
    y: float = 0.5
    icon: str = "pin"
    active: bool = True
    phase_ids: list[int] = []


@router.post("/maps")
def create_map(
    data: MapRequest,
    user=Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    if not data.name.strip():
        raise HTTPException(
            status_code=400,
            detail="Map name is required.",
        )

    game_map = GameMap(
        programme_id=programme.id,
        name=data.name.strip(),
        description=data.description.strip() if data.description else None,
        background_image=(
            data.background_image.strip()
            if data.background_image
            else None
        ),
        active=data.active,
    )

    db.add(game_map)
    db.commit()
    db.refresh(game_map)

    audit(
        db,
        user.id,
        "map.created",
        f"map_id={game_map.id};name={game_map.name}",
    )
    db.commit()

    return {
        "success": True,
        "id": game_map.id,
    }


@router.put("/maps/{map_id}")
def update_map(
    map_id: int,
    data: MapRequest,
    user=Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    game_map = (
        db.query(GameMap)
        .filter(
            GameMap.id == map_id,
            GameMap.programme_id == programme.id,
        )
        .first()
    )

    if not game_map:
        raise HTTPException(
            status_code=404,
            detail="Map not found.",
        )

    if not data.name.strip():
        raise HTTPException(
            status_code=400,
            detail="Map name is required.",
        )

    game_map.name = data.name.strip()
    game_map.description = (
        data.description.strip()
        if data.description
        else None
    )
    game_map.background_image = (
        data.background_image.strip()
        if data.background_image
        else None
    )
    game_map.active = data.active

    db.commit()

    audit(
        db,
        user.id,
        "map.updated",
        f"map_id={game_map.id};name={game_map.name}",
    )
    db.commit()

    return {
        "success": True,
        "id": game_map.id,
    }


@router.delete("/maps/{map_id}")
def delete_map(
    map_id: int,
    user=Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    game_map = (
        db.query(GameMap)
        .filter(
            GameMap.id == map_id,
            GameMap.programme_id == programme.id,
        )
        .first()
    )

    if not game_map:
        raise HTTPException(
            status_code=404,
            detail="Map not found.",
        )

    db.delete(game_map)

    audit(
        db,
        user.id,
        "map.deleted",
        f"map_id={map_id}",
    )

    db.commit()

    return {
        "success": True,
        "id": map_id,
    }


@router.post("/maps/{map_id}/locations")
def create_map_location(
    map_id: int,
    data: MapLocationRequest,
    user=Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    game_map = (
        db.query(GameMap)
        .filter(
            GameMap.id == map_id,
            GameMap.programme_id == programme.id,
        )
        .first()
    )

    if not game_map:
        raise HTTPException(
            status_code=404,
            detail="Map not found.",
        )

    if not data.name.strip():
        raise HTTPException(
            status_code=400,
            detail="Location name is required.",
        )

    if not 0 <= data.x <= 1 or not 0 <= data.y <= 1:
        raise HTTPException(
            status_code=400,
            detail="Location coordinates must be between 0 and 1.",
        )

    location = MapLocation(
        map_id=game_map.id,
        name=data.name.strip(),
        description=data.description.strip() if data.description else None,
        x=data.x,
        y=data.y,
        icon=data.icon.strip() or "pin",
        active=data.active,
    )

    db.add(location)
    db.flush()

    phases = (
        db.query(Phase)
        .filter(
            Phase.programme_id == programme.id,
            Phase.id.in_(data.phase_ids),
        )
        .all()
        if data.phase_ids
        else []
    )

    for phase in phases:
        location.phase_links.append(
            PhaseLocation(
                phase_id=phase.id,
                location_id=location.id,
            )
        )

    audit(
        db,
        user.id,
        "map.location.created",
        f"map_id={map_id};location_id={location.id};name={location.name}",
    )

    db.commit()

    return {
        "success": True,
        "id": location.id,
    }


@router.put("/maps/{map_id}/locations/{location_id}")
def update_map_location(
    map_id: int,
    location_id: int,
    data: MapLocationRequest,
    user=Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    location = (
        db.query(MapLocation)
        .join(GameMap, GameMap.id == MapLocation.map_id)
        .filter(
            MapLocation.id == location_id,
            MapLocation.map_id == map_id,
            GameMap.programme_id == programme.id,
        )
        .first()
    )

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Location not found.",
        )

    if not data.name.strip():
        raise HTTPException(
            status_code=400,
            detail="Location name is required.",
        )

    if not 0 <= data.x <= 1 or not 0 <= data.y <= 1:
        raise HTTPException(
            status_code=400,
            detail="Location coordinates must be between 0 and 1.",
        )

    location.name = data.name.strip()
    location.description = (
        data.description.strip()
        if data.description
        else None
    )
    location.x = data.x
    location.y = data.y
    location.icon = data.icon.strip() or "pin"
    location.active = data.active

    db.query(PhaseLocation).filter(
        PhaseLocation.location_id == location.id,
    ).delete(
        synchronize_session=False,
    )

    phases = (
        db.query(Phase)
        .filter(
            Phase.programme_id == programme.id,
            Phase.id.in_(data.phase_ids),
        )
        .all()
        if data.phase_ids
        else []
    )

    for phase in phases:
        db.add(
            PhaseLocation(
                phase_id=phase.id,
                location_id=location.id,
            )
        )

    audit(
        db,
        user.id,
        "map.location.updated",
        f"map_id={map_id};location_id={location.id};name={location.name}",
    )

    db.commit()

    return {
        "success": True,
        "id": location.id,
    }


@router.delete("/maps/{map_id}/locations/{location_id}")
def delete_map_location(
    map_id: int,
    location_id: int,
    user=Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    location = (
        db.query(MapLocation)
        .join(GameMap, GameMap.id == MapLocation.map_id)
        .filter(
            MapLocation.id == location_id,
            MapLocation.map_id == map_id,
            GameMap.programme_id == programme.id,
        )
        .first()
    )

    if not location:
        raise HTTPException(
            status_code=404,
            detail="Location not found.",
        )

    db.delete(location)

    audit(
        db,
        user.id,
        "map.location.deleted",
        f"map_id={map_id};location_id={location_id}",
    )

    db.commit()

    return {
        "success": True,
        "id": location_id,
    }


@router.get("/themes")
def admin_themes(
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    themes = (
        db.query(Theme)
        .filter(
            Theme.programme_id == programme.id
        )
        .order_by(
            Theme.name.asc(),
            Theme.id.asc(),
        )
        .all()
    )

    return [
        theme_response(theme, programme)
        for theme in themes
    ]


@router.post("/themes")
def create_theme(
    data: ThemeRequest,
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    name = data.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Theme name is required.",
        )

    duplicate = (
        db.query(Theme)
        .filter(
            Theme.programme_id == programme.id,
            Theme.name == name,
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="A theme with this name already exists.",
        )

    theme = Theme(
        programme_id=programme.id,
        name=name,
        primary=data.primary.strip(),
        secondary=data.secondary.strip(),
        accent=data.accent.strip(),
        background=data.background.strip(),
        surface=data.surface.strip(),
        text=data.text.strip(),
        logo_url=(
            data.logo_url.strip()
            if data.logo_url
            else None
        ),
        font_family=(
            data.font_family.strip()
            if data.font_family
            else None
        ),
        active=True,
    )

    db.add(theme)
    db.flush()

    audit(
        db,
        user.id,
        "theme.created",
        (
            f"id={theme.id};"
            f"name={theme.name}"
        ),
    )

    db.commit()

    return {
        "success": True,
        "id": theme.id,
    }


@router.put("/themes/{theme_id}")
def update_theme(
    theme_id: int,
    data: ThemeRequest,
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    theme = (
        db.query(Theme)
        .filter(
            Theme.id == theme_id,
            Theme.programme_id == programme.id,
        )
        .first()
    )

    if not theme:
        raise HTTPException(
            status_code=404,
            detail="Theme not found.",
        )

    name = data.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Theme name is required.",
        )

    duplicate = (
        db.query(Theme)
        .filter(
            Theme.programme_id == programme.id,
            Theme.name == name,
            Theme.id != theme.id,
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="A theme with this name already exists.",
        )

    theme.name = name
    theme.primary = data.primary.strip()
    theme.secondary = data.secondary.strip()
    theme.accent = data.accent.strip()
    theme.background = data.background.strip()
    theme.surface = data.surface.strip()
    theme.text = data.text.strip()
    theme.logo_url = (
        data.logo_url.strip()
        if data.logo_url
        else None
    )
    theme.font_family = (
        data.font_family.strip()
        if data.font_family
        else None
    )

    audit(
        db,
        user.id,
        "theme.updated",
        (
            f"id={theme.id};"
            f"name={theme.name}"
        ),
    )

    db.commit()

    return {
        "success": True,
        "id": theme.id,
    }


@router.post("/themes/{theme_id}/activate")
def activate_theme(
    theme_id: int,
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    theme = (
        db.query(Theme)
        .filter(
            Theme.id == theme_id,
            Theme.programme_id == programme.id,
            Theme.active == True,
        )
        .first()
    )

    if not theme:
        raise HTTPException(
            status_code=404,
            detail="Theme not found.",
        )

    db.query(Theme).filter(
        Theme.programme_id == programme.id,
    ).update(
        {
            Theme.active: False,
        },
        synchronize_session=False,
    )

    theme.active = True
    programme.active_theme_id = theme.id

    audit(
        db,
        user.id,
        "theme.activated",
        (
            f"id={theme.id};"
            f"name={theme.name}"
        ),
    )

    db.commit()

    return {
        "success": True,
        "id": theme.id,
    }


# ============================================================
# STAFF GROUP MANAGEMENT
# ============================================================

class StaffGroupCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    player_ids: list[int] = Field(
        default_factory=list,
        max_length=100,
    )


class StaffGroupUpdateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    active: bool = True


def _staff_group(
    db: Session,
    group_id: int,
    programme_id: int,
) -> YouthGroup:
    group = (
        db.query(YouthGroup)
        .filter(
            YouthGroup.id == group_id,
            YouthGroup.programme_id == programme_id,
        )
        .first()
    )

    if group is None:
        raise HTTPException(
            status_code=404,
            detail="Group not found.",
        )

    return group


def _group_payload(
    db: Session,
    group: YouthGroup,
):
    players = (
        db.query(Player)
        .filter(
            Player.group_id == group.id,
            Player.active == True,
        )
        .order_by(Player.gamertag.asc())
        .all()
    )

    return {
        "id": group.id,
        "programme_id": group.programme_id,
        "name": group.name,
        "active": group.active,
        "player_count": len(players),
        "players": [
            {
                "id": player.id,
                "gamertag": player.gamertag,
                "avatar": player.avatar,
                "active": player.active,
                "suspended": player.suspended,
                "group_id": player.group_id,
                "xp": player_xp(
                    db,
                    player.id,
                ),
            }
            for player in players
        ],
    }


@router.get("/groups")
def staff_groups(
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    groups = (
        db.query(YouthGroup)
        .filter(
            YouthGroup.programme_id == programme.id,
        )
        .order_by(
            YouthGroup.active.desc(),
            YouthGroup.name.asc(),
        )
        .all()
    )

    return [
        _group_payload(db, group)
        for group in groups
    ]


@router.post("/groups")
def create_staff_group(
    data: StaffGroupCreateRequest,
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    name = data.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Group name is required.",
        )

    duplicate = (
        db.query(YouthGroup)
        .filter(
            YouthGroup.programme_id == programme.id,
            YouthGroup.name == name,
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="A group with this name already exists.",
        )

    player_ids = list(dict.fromkeys(data.player_ids))

    players = []

    if player_ids:
        players = (
            db.query(Player)
            .filter(
                Player.id.in_(player_ids),
                Player.active == True,
            )
            .all()
        )

        found_ids = {player.id for player in players}
        missing_ids = [
            player_id
            for player_id in player_ids
            if player_id not in found_ids
        ]

        if missing_ids:
            raise HTTPException(
                status_code=400,
                detail=(
                    "One or more selected players "
                    "could not be found or are inactive."
                ),
            )

    group = YouthGroup(
        programme_id=programme.id,
        name=name,
        active=True,
    )

    db.add(group)
    db.flush()

    for player in players:
        player.group_id = group.id

    audit(
        db,
        user.id,
        "group.created",
        (
            f"group_id={group.id};"
            f"name={group.name};"
            f"player_ids={player_ids}"
        ),
    )

    db.commit()
    db.refresh(group)

    return _group_payload(
        db,
        group,
    )


@router.put("/groups/{group_id}")
def update_staff_group(
    group_id: int,
    data: StaffGroupUpdateRequest,
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    group = _staff_group(
        db,
        group_id,
        programme.id,
    )

    name = data.name.strip()

    if not name:
        raise HTTPException(
            status_code=400,
            detail="Group name is required.",
        )

    duplicate = (
        db.query(YouthGroup)
        .filter(
            YouthGroup.programme_id == programme.id,
            YouthGroup.name == name,
            YouthGroup.id != group.id,
        )
        .first()
    )

    if duplicate:
        raise HTTPException(
            status_code=409,
            detail="A group with this name already exists.",
        )

    old_name = group.name
    old_active = group.active

    group.name = name
    group.active = data.active

    audit(
        db,
        user.id,
        "group.updated",
        (
            f"group_id={group.id};"
            f"old_name={old_name};"
            f"new_name={group.name};"
            f"old_active={old_active};"
            f"new_active={group.active}"
        ),
    )

    db.commit()
    db.refresh(group)

    return _group_payload(
        db,
        group,
    )


@router.post("/groups/{group_id}/players/{player_id}")
def add_player_to_staff_group(
    group_id: int,
    player_id: int,
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    group = _staff_group(
        db,
        group_id,
        programme.id,
    )

    if not group.active:
        raise HTTPException(
            status_code=400,
            detail="Cannot assign a player to an inactive group.",
        )

    player = (
        db.query(Player)
        .filter(
            Player.id == player_id,
            Player.active == True,
        )
        .first()
    )

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player not found.",
        )

    previous_group_id = player.group_id

    player.group_id = group.id

    audit(
        db,
        user.id,
        "group.player_assigned",
        (
            f"group_id={group.id};"
            f"player_id={player.id};"
            f"previous_group_id={previous_group_id}"
        ),
    )

    db.commit()

    return {
        "success": True,
        "group_id": group.id,
        "player_id": player.id,
        "previous_group_id": previous_group_id,
    }


@router.delete(
    "/groups/{group_id}/players/{player_id}"
)
def remove_player_from_staff_group(
    group_id: int,
    player_id: int,
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    group = _staff_group(
        db,
        group_id,
        programme.id,
    )

    player = (
        db.query(Player)
        .filter(
            Player.id == player_id,
            Player.active == True,
            Player.group_id == group.id,
        )
        .first()
    )

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Player is not a member of this group.",
        )

    player.group_id = None

    audit(
        db,
        user.id,
        "group.player_removed",
        (
            f"group_id={group.id};"
            f"player_id={player.id}"
        ),
    )

    db.commit()

    return {
        "success": True,
        "group_id": group.id,
        "player_id": player.id,
        "group_id_after": None,
    }



# ============================================================
# SIMPLE ADMIN DATA ENDPOINTS
# ============================================================

@router.get("/players")
def admin_players(
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    players = (
        db.query(Player)
        .join(
            YouthGroup,
            Player.group_id
            == YouthGroup.id,
            isouter=True,
        )
        .filter(
            Player.active == True,
        )
        .order_by(
            Player.gamertag.asc()
        )
        .all()
    )

    return [
        {
            "id": player.id,
            "gamertag": player.gamertag,
            "avatar": player.avatar,
            "active": player.active,
            "suspended": player.suspended,
            "public_visible": (
                player.public_visible
            ),
            "group_id": player.group_id,
            "xp": player_xp(
                db,
                player.id,
            ),
        }
        for player in players
    ]


@router.get("/themes")
def admin_themes(
    user=Depends(
        require_roles("admin")
    ),
    db: Session = Depends(get_db),
):
    programme = get_programme(db)

    themes = (
        db.query(Theme)
        .filter(
            Theme.programme_id
            == programme.id
        )
        .order_by(
            Theme.name.asc()
        )
        .all()
    )

    return [
        {
            "id": theme.id,
            "name": theme.name,
            "primary": theme.primary,
            "secondary": theme.secondary,
            "accent": theme.accent,
            "background": theme.background,
            "surface": theme.surface,
            "text": theme.text,
            "logo_url": theme.logo_url,
            "font_family": theme.font_family,
            "active": theme.active,
            "selected": (
                theme.id
                == programme.active_theme_id
            ),
        }
        for theme in themes
    ]



# ============================================================
# YOUTH WORKER SKILL PLANS
# ============================================================

class SkillPlanMilestoneRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    required_xp: int = Field(
        ...,
        ge=1,
        le=1_000_000,
    )

    reward_description: str | None = Field(
        default=None,
        max_length=500,
    )


class SkillPlanCreateRequest(BaseModel):
    player_id: int

    name: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    description: str | None = Field(
        default=None,
        max_length=2000,
    )

    milestones: list[SkillPlanMilestoneRequest] = Field(
        ...,
        min_length=1,
        max_length=3,
    )


def _skill_plan_payload(
    tree: SkillTree,
    gamertag: str | None = None,
):
    return {
        "id": tree.id,
        "player_id": tree.player_id,
        "gamertag": gamertag,
        "name": tree.name,
        "description": tree.description,
        "active": tree.active,
        "completed": tree.completed,
        "completed_at": (
            tree.completed_at.isoformat()
            if tree.completed_at
            else None
        ),
        "current_xp": tree.current_xp,
        "tree_number": tree.tree_number,
        "milestones": [
            {
                "id": milestone.id,
                "name": milestone.name,
                "required_xp": milestone.required_xp,
                "sort_order": milestone.sort_order,
                "reward_description": (
                    milestone.reward_description
                ),
                "completed": milestone.completed,
                "completed_at": (
                    milestone.completed_at.isoformat()
                    if milestone.completed_at
                    else None
                ),
            }
            for milestone in tree.milestones
        ],
    }


@router.get("/skill-plans")
def get_skill_plans(
    player_id: int | None = None,
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    query = (
        db.query(SkillTree)
        .join(
            Player,
            SkillTree.player_id == Player.id,
        )
        .filter(
            Player.active == True,
        )
    )

    if player_id is not None:
        query = query.filter(
            SkillTree.player_id == player_id,
        )

    trees = (
        query
        .order_by(
            SkillTree.active.desc(),
            SkillTree.completed.asc(),
            SkillTree.player_id.asc(),
            SkillTree.tree_number.asc(),
            SkillTree.id.asc(),
        )
        .all()
    )

    return [
        _skill_plan_payload(
            tree,
            tree.player.gamertag,
        )
        for tree in trees
    ]


@router.post("/skill-plans")
def create_skill_plan(
    data: SkillPlanCreateRequest,
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    player = (
        db.query(Player)
        .filter(
            Player.id == data.player_id,
            Player.active == True,
        )
        .first()
    )

    if player is None:
        raise HTTPException(
            status_code=404,
            detail="Young person not found.",
        )

    active_tree = (
        db.query(SkillTree)
        .filter(
            SkillTree.player_id == player.id,
            SkillTree.active == True,
            SkillTree.completed == False,
        )
        .first()
    )

    if active_tree is not None:
        raise HTTPException(
            status_code=409,
            detail=(
                "This young person already has an active "
                "skill plan. Complete or archive it first."
            ),
        )

    milestone_xp = [
        milestone.required_xp
        for milestone in data.milestones
    ]

    if milestone_xp != sorted(milestone_xp):
        raise HTTPException(
            status_code=400,
            detail=(
                "Milestone XP thresholds must increase."
            ),
        )

    if len(set(milestone_xp)) != len(milestone_xp):
        raise HTTPException(
            status_code=400,
            detail=(
                "Milestone XP thresholds must be different."
            ),
        )

    previous_trees = (
        db.query(SkillTree)
        .filter(
            SkillTree.player_id == player.id,
        )
        .all()
    )

    next_tree_number = (
        max(
            (
                tree.tree_number
                for tree in previous_trees
            ),
            default=0,
        )
        + 1
    )

    tree = SkillTree(
        player_id=player.id,
        name=data.name.strip(),
        description=(
            data.description.strip()
            if data.description
            else None
        ),
        active=True,
        completed=False,
        current_xp=0,
        tree_number=next_tree_number,
    )

    db.add(tree)
    db.flush()

    for sort_order, milestone in enumerate(
        data.milestones,
        start=1,
    ):
        db.add(
            SkillMilestone(
                skill_tree_id=tree.id,
                name=milestone.name.strip(),
                required_xp=milestone.required_xp,
                sort_order=sort_order,
                reward_description=(
                    milestone.reward_description.strip()
                    if milestone.reward_description
                    else None
                ),
                completed=False,
            )
        )

    audit(
        db,
        user.id,
        "skill_tree.created",
        (
            f"skill_tree_id={tree.id};"
            f"player_id={player.id};"
            f"tree_number={tree.tree_number}"
        ),
    )

    db.commit()
    db.refresh(tree)

    return _skill_plan_payload(
        tree,
        player.gamertag,
    )


@router.post("/skill-plans/{skill_tree_id}/archive")
def archive_skill_plan(
    skill_tree_id: int,
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    tree = (
        db.query(SkillTree)
        .join(
            Player,
            SkillTree.player_id == Player.id,
        )
        .filter(
            SkillTree.id == skill_tree_id,
            Player.active == True,
        )
        .first()
    )

    if tree is None:
        raise HTTPException(
            status_code=404,
            detail="Skill plan not found.",
        )

    if not tree.active:
        raise HTTPException(
            status_code=409,
            detail="Skill plan is already archived.",
        )

    tree.active = False

    audit(
        db,
        user.id,
        "skill_tree.archived",
        (
            f"skill_tree_id={tree.id};"
            f"player_id={tree.player_id}"
        ),
    )

    db.commit()

    return {
        "success": True,
        "id": tree.id,
        "active": False,
    }


# ============================================================
# COMMUNITY AWARDS
# ============================================================

@router.get("/community-awards")
def list_community_awards(
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    """
    Staff-only list of community award nominations.

    Submitter information is intentionally only exposed here,
    behind staff authentication.
    """

    awards = (
        db.query(CommunityAward)
        .order_by(
            CommunityAward.created_at.desc(),
        )
        .all()
    )

    return [
        {
            "id": award.id,
            "player_id": award.player_id,
            "group_id": award.group_id,
            "category": award.category,
            "description": award.description,
            "submitted_by_name": award.submitted_by_name,
            "submitted_by_contact": award.submitted_by_contact,
            "status": award.status,
            "xp": award.xp,
            "created_at": (
                award.created_at.isoformat()
                if award.created_at
                else None
            ),
        }
        for award in awards
    ]


# ============================================================
# COMMUNITY AWARDS
# ============================================================

class CommunityAwardReviewRequest(BaseModel):
    status: str = Field(
        ...,
        pattern="^(approved|rejected)$",
    )

    # Required when approving a community recognition.
    # The Youth Worker decides how much XP the recognition deserves.
    xp: int | None = Field(
        default=None,
        ge=1,
        le=10000,
    )


@router.post("/community-awards/{award_id}/review")
def review_community_award(
    award_id: int,
    data: CommunityAwardReviewRequest,
    user=Depends(
        require_roles(
            "admin",
            "youth_worker",
        )
    ),
    db: Session = Depends(get_db),
):
    award = (
        db.query(CommunityAward)
        .filter(
            CommunityAward.id == award_id,
        )
        .first()
    )

    if award is None:
        raise HTTPException(
            status_code=404,
            detail="Community award not found.",
        )

    if award.status != "pending":
        raise HTTPException(
            status_code=409,
            detail=(
                "This community award has already been reviewed."
            ),
        )

    programme = (
        db.query(Programme)
        .filter(
            Programme.id == award.programme_id,
        )
        .first()
    )

    if programme is None:
        raise HTTPException(
            status_code=404,
            detail="Programme not found.",
        )

    if data.status == "approved":
        if data.xp is None:
            raise HTTPException(
                status_code=400,
                detail="XP points are required when approving a community award.",
            )

        if data.xp < 1:
            raise HTTPException(
                status_code=400,
                detail="XP points must be greater than zero.",
            )

        if award.player_id is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Group community awards cannot yet be "
                    "converted into player XP transactions."
                ),
            )

        player = (
            db.query(Player)
            .filter(
                Player.id == award.player_id,
                Player.active == True,
            )
            .first()
        )

        if player is None:
            raise HTTPException(
                status_code=400,
                detail="Awarded player is no longer active.",
            )

        transaction = award_xp(
            db,
            programme_id=award.programme_id,
            player_id=award.player_id,
            amount=data.xp,
            group_amount=data.xp,
            transaction_type="community_award",
            reason=(
                f"Community award: {award.category}"
            ),
            reference_type="community_award",
            reference_id=award.id,
            created_by=user.id,
        )

        # Persist the XP amount chosen by the Youth Worker.
        award.xp = data.xp

        award.status = "approved"
        award.reviewed_by = user.id
        award.reviewed_at = __import__(
            "datetime"
        ).datetime.utcnow()

        audit(
            db,
            user.id,
            "community_award.approved",
            (
                f"award_id={award.id};"
                f"player_id={award.player_id};"
                f"xp={data.xp};"
                f"transaction_id={transaction.id}"
            ),
        )

    else:
        award.status = "rejected"
        award.reviewed_by = user.id
        award.reviewed_at = __import__(
            "datetime"
        ).datetime.utcnow()

        audit(
            db,
            user.id,
            "community_award.rejected",
            f"award_id={award.id}",
        )

    db.commit()

    return {
        "success": True,
        "id": award.id,
        "status": award.status,
    }
