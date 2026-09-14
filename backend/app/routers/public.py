from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db.models import (
    Programme,
    Phase,
    Theme,
    GameMap,
    MapLocation,
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

    return {
        "programme": {
            "id": programme.id,
            "name": programme.name,
            "target_xp": programme.target_xp,
            "weekly_target_xp": programme.weekly_target_xp,
        },
        "group_xp": group_xp(db),
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
