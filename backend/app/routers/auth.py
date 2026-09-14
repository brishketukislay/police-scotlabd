from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import (
    create_session,
    get_current_user,
    verify_password,
)
from ..core.config import settings
from ..db.database import get_db
from ..db.models import User


router = APIRouter(
    prefix="/api/auth",
    tags=["auth"],
)


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(
    data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    user = (
        db.query(User)
        .filter(User.username == data.username)
        .first()
    )

    if not user or not verify_password(
        data.password,
        user.password_hash,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid username or password",
        )

    if not user.active:
        raise HTTPException(
            status_code=403,
            detail="Account disabled",
        )

    user.last_login_at = datetime.utcnow()
    db.commit()

    token = create_session(user.id)

    response.set_cookie(
        key=settings.session_cookie_name,
        value=token,
        max_age=settings.session_max_age_seconds,
        httponly=settings.session_cookie_http_only,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_same_site,
    )

    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        key=settings.session_cookie_name,
        secure=settings.session_cookie_secure,
        httponly=settings.session_cookie_http_only,
        samesite=settings.session_cookie_same_site,
    )
    return {"success": True}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
    }
