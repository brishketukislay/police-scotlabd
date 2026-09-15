from datetime import datetime, timedelta, timezone

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy import func, text
from sqlalchemy.orm import Session


from ..db.database import get_db

from ..db.models import (
        Reward,
        PlayerReward,
    Player,
    YouthGroup,
    Programme,
    Theme,
    GameMap,
    MapLocation,
    Phase,
    Badge,
    PlayerBadge,
    SkillTree,
    SkillMilestone,
    Challenge,
    XPTransaction,
    Attendance,
    AttendanceSession,
    PlayerXPBalance,
        DrawingGame,
        DrawingGameAssignment,
        DrawingGameAttempt,
)

from ..auth import require_roles

from ..services.xp import (
    player_xp,
    group_xp,
)


router = APIRouter(
    prefix="/api/player",
    tags=["player"],
)


FIXED_AVATARS = [
    {
        "id": "avatar-01",
        "name": "Fox",
        "emoji": "🦊",
    },
    {
        "id": "avatar-02",
        "name": "Bear",
        "emoji": "🐻",
    },
    {
        "id": "avatar-03",
        "name": "Frog",
        "emoji": "🐸",
    },
    {
        "id": "avatar-04",
        "name": "Robot",
        "emoji": "🤖",
    },
    {
        "id": "avatar-05",
        "name": "Tiger",
        "emoji": "🐯",
    },
    {
        "id": "avatar-06",
        "name": "Wolf",
        "emoji": "🐺",
    },
    {
        "id": "avatar-07",
        "name": "Panda",
        "emoji": "🐼",
    },
    {
        "id": "avatar-08",
        "name": "Dragon",
        "emoji": "🐲",
    },
    {
        "id": "avatar-09",
        "name": "Alien",
        "emoji": "👾",
    },
    {
        "id": "avatar-10",
        "name": "Octopus",
        "emoji": "🐙",
    },
    {
        "id": "avatar-11",
        "name": "Cat",
        "emoji": "🐱",
    },
    {
        "id": "avatar-12",
        "name": "Penguin",
        "emoji": "🐧",
    },
]


@router.get("/avatars")
def avatars(
    user=Depends(
        require_roles("player")
    ),
):
    return FIXED_AVATARS


@router.get("/dashboard")
def dashboard(
    user=Depends(
        require_roles("player")
    ),
    db: Session = Depends(get_db),
):

    player = (
        db.query(Player)
        .filter(
            Player.user_id == user.id
        )
        .first()
    )

    if not player:
        raise HTTPException(
            status_code=404,
            detail="Player profile not found",
        )

    programme = (
        db.query(Programme)
        .filter(
            Programme.active == True
        )
        .first()
    )
    # Drawing game assignments
    drawing_game_assignments = []
    if programme:
        assignment_rows = db.execute(
            text(
                """
                SELECT
                    a.id AS assignment_id,
                    a.game_id,
                    g.name,
                    g.description,
                    g.shape,
                    g.config
                FROM drawing_game_assignments a
                JOIN drawing_games g ON g.id = a.game_id
                WHERE a.player_id = :player_id
                  AND a.programme_id = :programme_id
                  AND a.status = 'assigned'
                  AND g.active = 1
                """
            ),
            {"player_id": player.id, "programme_id": programme.id},
        ).mappings().all()
        drawing_game_assignments = [dict(row) for row in assignment_rows]

    theme = (
        db.get(
            Theme,
            programme.active_theme_id,
        )
        if programme and programme.active_theme_id
        else None
    )

    game_map = (
        db.get(
            GameMap,
            programme.active_map_id,
        )
        if programme and programme.active_map_id
        else None
    )

    phases = []

    if programme:

        phases = (
            db.query(Phase)
            .filter(
                Phase.programme_id
                == programme.id,
                Phase.active == True,
            )
            .order_by(
                Phase.sort_order
            )
            .all()
        )

    current_phase = (
        phases[0]
        if phases
        else None
    )

    locations = []

    if game_map:

        locations = (
            db.query(MapLocation)
            .filter(
                MapLocation.map_id
                == game_map.id,
                MapLocation.active == True,
            )
            .all()
        )

    badges = (
    db.query(PlayerBadge)
    .filter(
        PlayerBadge.player_id
        == player.id
    )
    .all()
)


    skill = (
        db.query(SkillTree)
        .filter(
            SkillTree.player_id
            == player.id,
            SkillTree.active == True,
            SkillTree.completed == False,
        )
        .first()
    )

    milestones = []

    if skill:

        milestones = (
            db.query(
                SkillMilestone
            )
            .filter(
                SkillMilestone.skill_tree_id
                == skill.id
            )
            .order_by(
                SkillMilestone.required_xp
            )
            .all()
        )

    # Completed skill trees remain linked to the young person
    # and are shown separately from the current active tree.
    completed_skills = (
        db.query(SkillTree)
        .filter(
            SkillTree.player_id == player.id,
            SkillTree.completed == True,
        )
        .order_by(
            SkillTree.completed_at.desc(),
            SkillTree.id.desc(),
        )
        .all()
    )

    challenges = (
        db.query(Challenge)
        .filter(
            Challenge.active == True
        )
        .all()
    )

    player_total = player_xp(
        db,
        player.id,
    )

    # ------------------------------------------------------------
    # WEEKLY PLAYER STATS
    # ------------------------------------------------------------
    now = datetime.now(timezone.utc)
    week_start = now - timedelta(days=now.weekday())
    week_start = week_start.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    weekly_xp = (
        db.query(XPTransaction)
        .filter(
            XPTransaction.player_id == player.id,
            XPTransaction.programme_id == (
                programme.id if programme else -1
            ),
            XPTransaction.created_at >= week_start,
            XPTransaction.amount > 0,
        )
        .with_entities(
            func.coalesce(
                func.sum(XPTransaction.amount),
                0,
            )
        )
        .scalar()
        or 0
    )

    # "Activity" on the player dashboard means actual attendance
    # sessions, not XP transactions. A single session may generate
    # multiple XP ledger entries.
    activity_count = 0

    if programme:
        activity_count = (
            db.query(Attendance.id)
            .join(
                AttendanceSession,
                Attendance.session_id == AttendanceSession.id,
            )
            .filter(
                Attendance.player_id == player.id,
                AttendanceSession.programme_id == programme.id,
                Attendance.checked_in_at >= week_start,
            )
            .count()
        )

    achievements = [
        {
            "id": player_badge.id,
            "name": badge.name,
            "description": badge.description,
            "colour": badge.colour,
        }
        for player_badge in badges
        for badge in [player_badge.badge]
        if badge is not None
    ]

    # ------------------------------------------------------------
    # PLAYER RANK
    #
    # Rank only against active, public-visible players in the
    # player's active programme.  Do not expose other players'
    # identities in the response.
    # ------------------------------------------------------------
    leaderboard = []

    if programme:
        ranked_players = (
            db.query(
                Player.id,
                func.coalesce(
                    PlayerXPBalance.current_xp,
                    0,
                ).label("xp"),
            )
            .outerjoin(
                PlayerXPBalance,
                PlayerXPBalance.player_id == Player.id,
            )
            .filter(
                Player.programme_id == programme.id,
                Player.active == True,
                Player.public_visible == True,
            )
            .order_by(
                func.coalesce(
                    PlayerXPBalance.current_xp,
                    0,
                ).desc(),
                Player.id.asc(),
            )
            .all()
        )

        player_rank = next(
            (
                index + 1
                for index, item in enumerate(ranked_players)
                if item.id == player.id
            ),
            None,
        )

        leaderboard_size = len(ranked_players)

        # Do not expose the identities of other young people.
        # The player only needs their rank and the total leaderboard size.
        leaderboard = [
            {
                "id": item.id,
                "xp": int(item.xp or 0),
            }
            for item in ranked_players
        ]
    else:
        ranked_players = []
        player_rank = None
        leaderboard_size = 0

    # ------------------------------------------------------------
    # PERFORMANCE
    #
    # Keep this aggregate and youth-facing: the player can see
    # their own performance and their group's collective progress,
    # without exposing other young people's individual XP.
    # ------------------------------------------------------------

    group_performance = None

    if player.group_id is not None:
        current_group = db.get(
            YouthGroup,
            player.group_id,
        )

        if current_group is not None:
            all_groups = (
                db.query(YouthGroup)
                .filter(
                    YouthGroup.programme_id == programme.id,
                    YouthGroup.active == True,
                )
                .all()
            )

            ranked_groups = sorted(
                [
                    {
                        "id": group.id,
                        "name": group.name,
                        "xp": group_xp(
                            db,
                            group_id=group.id,
                        ),
                    }
                    for group in all_groups
                ],
                key=lambda item: (-item["xp"], item["name"].lower()),
            )

            rank = next(
                (
                    index + 1
                    for index, item in enumerate(ranked_groups)
                    if item["id"] == current_group.id
                ),
                None,
            )

            current_group_xp = group_xp(
                db,
                group_id=current_group.id,
            )

            active_member_count = (
                db.query(Player)
                .filter(
                    Player.group_id == current_group.id,
                    Player.active == True,
                )
                .count()
            )

            contribution_pct = (
                (player_total / current_group_xp) * 100
                if current_group_xp > 0
                else 0
            )

            target = (
                programme.target_xp
                if programme
                else 1500000
            )

            group_performance = {
                "id": current_group.id,
                "name": current_group.name,
                "xp": current_group_xp,
                "rank": rank,
                "member_count": active_member_count,
                "player_contribution_pct": round(
                    contribution_pct,
                    1,
                ),
                "target_xp": target,
                "progress_pct": round(
                    min(
                        100,
                        (current_group_xp / target) * 100,
                    )
                    if target
                    else 0,
                    1,
                ),
                "groups_ranked": len(ranked_groups),
            }

    # ------------------------------------------------------------
    # REWARDS
    #
    # Rewards are granted by the XP service when an XP transaction
    # causes the player to cross a configured threshold.
    #
    # The dashboard only reads the resulting PlayerReward records.
    # ------------------------------------------------------------

    active_rewards = []

    if programme:
        active_rewards = (
            db.query(Reward)
            .filter(
                Reward.programme_id == programme.id,
                Reward.active.is_(True),
            )
            .order_by(
                Reward.xp_threshold.asc(),
                Reward.id.asc(),
            )
            .all()
        )

    player_rewards = (
        db.query(PlayerReward)
        .filter(
            PlayerReward.player_id == player.id,
        )
        .all()
    )

    player_reward_by_id = {
        player_reward.reward_id: player_reward
        for player_reward in player_rewards
    }

    mystery_rewards = []

    for reward in active_rewards:
        player_reward = player_reward_by_id.get(
            reward.id
        )

        mystery_rewards.append({
            "id": reward.id,
            "name": reward.name,
            "xp_threshold": reward.xp_threshold,
            "thresholdXP": reward.xp_threshold,
            "reward_type": reward.reward_type,
            "value": reward.value,
            "active": reward.active,
            "unlocked": player_reward is not None,
            "claimed": (
                player_reward is not None
                and player_reward.status == "claimed"
            ),
            "status": (
                player_reward.status
                if player_reward is not None
                else "locked"
            ),
        })

    return {

        "player": {
            "id": player.id,
            "gamertag": player.gamertag,
            "avatar": player.avatar,
            "xp": player_total,
            "individual_xp": player_total,
            "weekly_xp": weekly_xp,
            "activity_count": activity_count,
            "achievements": achievements,
            "rank": player_rank,
            "rank_total": leaderboard_size,
        },

        "overview": {
            "target_xp": (
                programme.target_xp
                if programme
                else 0
            ),
            "weekly_target_xp": (
                programme.weekly_target_xp
                if programme
                else 0
            ),
        },

        "leaderboard": leaderboard,

        "mystery_rewards": mystery_rewards,

        "group_xp": (
            group_xp(
                db,
                group_id=player.group_id,
            )
            if player.group_id is not None
            else None
        ),

        "group": (
            {
                "id": player.group.id,
                "name": player.group.name,
            }
            if player.group is not None
            else None
        ),

        "performance": {
            "player_xp": player_total,
            "group": group_performance,
        },

        "target_xp": (
            programme.target_xp
            if programme
            else 1500000
        ),

        "programme": {
            "name": (
                programme.name
                if programme
                else "Youth Challenge"
            ),
        },

        "theme": (
            {
                "primary": theme.primary,
                "secondary": theme.secondary,
                "accent": theme.accent,
                "background": theme.background,
                "surface": theme.surface,
                "text": theme.text,
            }
            if theme
            else None
        ),

        "map": (
            {
                "id": game_map.id,
                "name": game_map.name,
                "background_image":
                    game_map.background_image,

                "locations": [
                    {
                        "id": location.id,
                        "name": location.name,
                        "description":
                            location.description,
                        "x": location.x,
                        "y": location.y,
                        "icon": location.icon,
                    }
                    for location in locations
                ],
            }
            if game_map
            else None
        ),

        "phase": (
            {
                "id": current_phase.id,
                "name": current_phase.name,
                "description":
                    current_phase.description,
                "colour":
                    current_phase.colour,
                "icon":
                    current_phase.icon,
            }
            if current_phase
            else None
        ),

        "badges": [
            {
                "name": badge.name,
                "description":
                    badge.description,
                "colour": badge.colour,
            }
            for badge in badges
        ],

        "skill_tree": (
            {
                "name": skill.name,
                "description":
                    skill.description,
                "xp": skill.current_xp,

                "milestones": [
                    {
                        "name": milestone.name,
                        "required_xp":
                            milestone.required_xp,
                        "completed":
                            milestone.completed,
                        "reward":
                            milestone.reward_description,
                    }
                    for milestone in milestones
                ],
            }
            if skill
            else None
        ),

        "completed_skill_trees": [
            {
                "id": tree.id,
                "player_id": tree.player_id,
                "name": tree.name,
                "description": tree.description,
                "xp": tree.current_xp,
                "active": tree.active,
                "completed": tree.completed,
                "completed_at": tree.completed_at,
                "milestones": [
                    {
                        "id": milestone.id,
                        "name": milestone.name,
                        "required_xp": milestone.required_xp,
                        "completed": milestone.completed,
                        "completed_at": milestone.completed_at,
                        "reward": milestone.reward_description,
                    }
                    for milestone in sorted(
                        tree.milestones,
                        key=lambda item: (
                            item.required_xp,
                            item.id,
                        ),
                    )
                ],
            }
            for tree in completed_skills
        ],

        "challenges": [
            {
                "id": challenge.id,
                "title": challenge.title,
                "description":
                    challenge.description,
                "participation_xp":
                    challenge.participation_xp,
                "elite_xp":
                    challenge.elite_xp,
                "winner_xp":
                    challenge.winner_xp,
                "group_xp":
                    challenge.group_xp,
            }
            for challenge in challenges
        ],
        "drawing_games": drawing_game_assignments

    }
