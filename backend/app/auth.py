from datetime import datetime, timedelta, timezone

import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidTokenError
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.models.user import User


bearer_scheme = HTTPBearer(auto_error=False)


def hash_password(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if len(password_bytes) > 72:
        raise ValueError("Password must be no longer than 72 UTF-8 bytes.")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt(rounds=12)).decode("ascii")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("ascii"))
    except (ValueError, TypeError):
        return False


def create_access_token(user: User) -> tuple[str, int]:
    secret = settings.JWT_SECRET_KEY
    if settings.AUTH_MODE != "jwt" or not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT authentication is not configured.",
        )

    expires_in = settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES * 60
    now = datetime.now(timezone.utc)
    token = jwt.encode(
        {
            "sub": str(user.id),
            "iat": now,
            "exp": now + timedelta(seconds=expires_in),
        },
        secret.get_secret_value(),
        algorithm="HS256",
    )
    return token, expires_in


def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User | None:
    if settings.AUTH_MODE == "disabled":
        return None

    if settings.AUTH_MODE == "proxy":
        email_identity = request.headers.get("x-auth-request-email", "").strip()
        user_identity = request.headers.get("x-auth-request-user", "").strip()
        identity = email_identity or user_identity
        if not identity:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication is required.",
            )
        identity_column = User.email if email_identity else User.username
        user = (
            db.query(User)
            .filter(func.lower(identity_column) == identity.lower())
            .first()
        )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="The authenticated identity is not registered.",
            )
        return user

    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    secret = settings.JWT_SECRET_KEY
    if not secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="JWT authentication is not configured.",
        )

    try:
        payload = jwt.decode(
            credentials.credentials,
            secret.get_secret_value(),
            algorithms=["HS256"],
        )
        user_id = int(payload["sub"])
    except (InvalidTokenError, KeyError, TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_current_user(
    user: User | None = Depends(get_current_user),
) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="A user-specific authenticated identity is required.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
