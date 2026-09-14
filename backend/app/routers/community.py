from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..db.database import get_db
from ..db.models import CommunityAward, Player, YouthGroup, Programme
from ..services.xp import award_xp


router = APIRouter(
    prefix="/api/community",
    tags=["community"],
)


def get_active_programme(db: Session) -> Programme:
    programme = (
        db.query(Programme)
        .filter(Programme.active == True)
        .first()
    )

    if programme is None:
        raise HTTPException(
            status_code=404,
            detail="No active programme configured.",
        )

    return programme


class CommunityAwardRequest(BaseModel):
    player_id: int | None = None
    group_id: int | None = None

    category: str = Field(
        ...,
        min_length=2,
        max_length=100,
    )

    description: str = Field(
        ...,
        min_length=10,
        max_length=5000,
    )

    submitted_by_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )

    submitted_by_contact: str = Field(
        ...,
        min_length=3,
        max_length=300,
    )


@router.post("/awards")
def create_community_award(
    data: CommunityAwardRequest,
    db: Session = Depends(get_db),
):
    if data.player_id is None and data.group_id is None:
        raise HTTPException(
            status_code=400,
            detail="A player or group must be nominated.",
        )

    if data.player_id is not None and data.group_id is not None:
        raise HTTPException(
            status_code=400,
            detail="Nominate either a player or a group, not both.",
        )

    programme = get_active_programme(db)

    category = data.category.strip()
    description = data.description.strip()
    submitted_by_name = data.submitted_by_name.strip()
    submitted_by_contact = data.submitted_by_contact.strip()

    if not category:
        raise HTTPException(
            status_code=400,
            detail="Category is required.",
        )

    if not description:
        raise HTTPException(
            status_code=400,
            detail="Description is required.",
        )

    if not submitted_by_name:
        raise HTTPException(
            status_code=400,
            detail="Submitter name is required.",
        )

    if not submitted_by_contact:
        raise HTTPException(
            status_code=400,
            detail="Submitter contact is required.",
        )

    if data.player_id is not None:
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
                detail="Player not found.",
            )

        if player.group_id is None:
            raise HTTPException(
                status_code=400,
                detail="Player is not assigned to a group.",
            )

    if data.group_id is not None:
        group = (
            db.query(YouthGroup)
            .filter(
                YouthGroup.id == data.group_id,
            )
            .first()
        )

        if group is None:
            raise HTTPException(
                status_code=404,
                detail="Group not found.",
            )

        if group.programme_id != programme.id:
            raise HTTPException(
                status_code=400,
                detail="Group does not belong to the active programme.",
            )

    award = CommunityAward(
        programme_id=programme.id,
        player_id=data.player_id,
        group_id=data.group_id,
        category=category,
        description=description,
        submitted_by_name=submitted_by_name,
        submitted_by_contact=submitted_by_contact,
        status="pending",
        xp=5000,
    )

    db.add(award)
    db.commit()
    db.refresh(award)

    return {
        "success": True,
        "id": award.id,
        "status": award.status,
    }
