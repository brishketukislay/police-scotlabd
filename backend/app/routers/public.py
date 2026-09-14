from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta, timezone

from ..db.database import get_db
from ..db.models import (
    Programme,
    Phase,
    Theme,
    GameMap,
    MapLocation,
    YouthGroup,
    Player,
    XPTransaction,
)

from ..services.xp import group_xp


router = APIRouter(
    prefix="/api/public",
    tags=["public"],
)


@router.get("/dashboard")
def public_dashboard(
    db: Session = Depends(get_db),
):
    programme = (
        db.query(Programme)
        .filter(Programme.active == True)
        .first()
    )

    if not programme:
        return {
            "programme": None,
            "group_xp": 0,
            "overall_progress": 0,
            "group_progress": [],
            "top_5_weekly_high_riser": [],
        }

    theme = (
        db.get(
            Theme,
            programme.active_theme_id,
        )
        if programme.active_theme_id
        else None
    )

    game_map = (
        db.get(
            GameMap,
            programme.active_map_id,
        )
        if programme.active_map_id
        else None
    )

    phases = (
        db.query(Phase)
        .filter(
            Phase.programme_id == programme.id,
            Phase.active == True,
        )
        .order_by(Phase.sort_order)
        .all()
    )

    locations = []

    if game_map:
        locations = (
            db.query(MapLocation)
            .filter(
                MapLocation.map_id == game_map.id,
                MapLocation.active == True,
            )
            .all()
        )

    # Total group XP (collective XP)
    total_group_xp = group_xp(db)

    # Overall progress towards programme target
    overall_progress = 0
    if programme.target_xp > 0:
        overall_progress = min((total_group_xp / programme.target_xp) * 100, 100)

    # Group progress: XP for each group in the programme
    group_progress = []
    groups = db.query(YouthGroup).filter(YouthGroup.programme_id == programme.id, YouthGroup.active == True).all()
    for group in groups:
        group_xp_amount = group_xp(db, group_id=group.id)
        group_progress.append({
            "id": group.id,
            "name": group.name,
            "xp": group_xp_amount,
            "progress_percentage": min((group_xp_amount / programme.target_xp) * 100, 100) if programme.target_xp > 0 else 0
        })

    # Top 5 weekly high-riser: top 5 players by individual XP gained in the last 7 days
    one_week_ago = datetime.now(timezone.utc) - timedelta(days=7)
    weekly_xp_results = (
        db.query(
            XPTransaction.player_id,
            func.sum(XPTransaction.amount).label("weekly_xp")
        )
        .filter(
            XPTransaction.programme_id == programme.id,
            XPTransaction.created_at >= one_week_ago,
            XPTransaction.amount > 0,  # Only positive XP for "riser"
        )
        .group_by(XPTransaction.player_id)
        .order_by(func.sum(XPTransaction.amount).desc())
        .limit(5)
        .all()
    )

    top_5_weekly_high_riser = []
    for player_id, weekly_xp in weekly_xp_results:
        player = db.get(Player, player_id)
        if player:
            top_5_weekly_high_riser.append({
                "player_id": player.id,
                "gamertag": player.gamertag,
                "avatar": player.avatar,
                "weekly_xp": int(weekly_xp) if weekly_xp else 0
            })

    return {
        "programme": {
            "id": programme.id,
            "name": programme.name,
            "target_xp": programme.target_xp,
            "weekly_target_xp": programme.weekly_target_xp,
        },
        "group_xp": total_group_xp,
        "overall_progress": round(overall_progress, 2),
        "group_progress": group_progress,
        "top_5_weekly_high_riser": top_5_weekly_high_riser,
        "theme": {
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
        } if theme else None,
        "phases": [
            {
                "id": phase.id,
                "name": phase.name,
                "description": phase.description,
                "colour": phase.colour,
                "icon": phase.icon,
            }
            for phase in phases
        ],
        "map": {
            "id": game_map.id,
            "name": game_map.name,
            "background_image": game_map.background_image,
            "locations": [
                {
                    "id": location.id,
                    "name": location.name,
                    "description": location.description,
                    "x": location.x,
                    "y": location.y,
                    "icon": location.icon,
                }
                for location in locations
            ],
        } if game_map else None,
    }