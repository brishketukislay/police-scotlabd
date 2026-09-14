from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..db.models import User
from ..auth import verify_password, create_session, get_current_user
from ..core.config import settings

router = APIRouter(prefix="/api/auth", tags=["auth"])


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == data.username).first()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    if not user.active:
        raise HTTPException(status_code=403, detail="Account disabled")

    user.last_login_at = datetime.utcnow()
    db.commit()

    token = create_session(user.id)

    response.set_cookie(
        settings.session_cookie_name,
        token,
        httponly=True,
        samesite="lax",
        secure=False,
        max_age=60 * 60 * 24 * 7,
    )

    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
    }


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(settings.session_cookie_name)
    return {"success": True}


@router.get("/me")
def me(user=Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "role": user.role,
    }
