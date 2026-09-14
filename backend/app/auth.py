from itsdangerous import (
    BadSignature,
    SignatureExpired,
    URLSafeTimedSerializer,
)
from passlib.hash import argon2
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from .core.config import settings
from .db.database import get_db
from .db.models import User


serializer = URLSafeTimedSerializer(settings.session_secret)


def hash_password(password: str) -> str:
    return argon2.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return argon2.verify(password, password_hash)


def create_session(user_id: int) -> str:
    return serializer.dumps({"user_id": user_id})


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):
    token = request.cookies.get(settings.session_cookie_name)

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
        )

    try:
        data = serializer.loads(
            token,
            max_age=settings.session_max_age_seconds,
        )
    except SignatureExpired:
        raise HTTPException(
            status_code=401,
            detail="Session expired",
        )
    except BadSignature:
        raise HTTPException(
            status_code=401,
            detail="Invalid session",
        )

    user = db.get(User, data["user_id"])

    if not user or not user.active:
        raise HTTPException(
            status_code=401,
            detail="Account unavailable",
        )

    return user


def require_roles(*roles):
    def dependency(user=Depends(get_current_user)):
        if user.role not in roles:
            raise HTTPException(
                status_code=403,
                detail="Insufficient permissions",
            )
        return user

    return dependency
