from unittest.mock import patch

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from pydantic import SecretStr

from app.auth import get_current_user
from app.core.config import settings
from app.database import get_db
from app.models.user import User
from app.routes.auth import router as auth_router


def create_client():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    User.__table__.create(bind=engine)
    test_session = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    def override_get_db():
        db = test_session()
        try:
            yield db
        finally:
            db.close()

    app = FastAPI()
    app.include_router(auth_router)
    app.dependency_overrides[get_db] = override_get_db

    @app.get("/protected")
    def protected_route(user=Depends(get_current_user)):
        return {"username": user.username}

    return TestClient(app), engine


def test_register_login_and_protected_route():
    client, engine = create_client()
    secret = SecretStr("test-secret-key-with-at-least-32-bytes")
    try:
        with (
            patch.object(settings, "AUTH_MODE", "jwt"),
            patch.object(settings, "JWT_SECRET_KEY", secret),
        ):
            registration = client.post(
                "/auth/register",
                json={
                    "username": "researcher",
                    "email": "researcher@example.com",
                    "password": "safe-password-123",
                },
            )
            assert registration.status_code == 201, registration.text
            assert "password_hash" not in registration.json()

            login = client.post(
                "/auth/login",
                json={
                    "username_or_email": "RESEARCHER",
                    "password": "safe-password-123",
                },
            )
            assert login.status_code == 200
            assert login.json()["token_type"] == "bearer"

            token = login.json()["access_token"]
            response = client.get(
                "/protected",
                headers={"Authorization": f"Bearer {token}"},
            )
            assert response.status_code == 200
            assert response.json() == {"username": "researcher"}

            duplicate = client.post(
                "/auth/register",
                json={
                    "username": "researcher",
                    "email": "another@example.com",
                    "password": "safe-password-123",
                },
            )
            assert duplicate.status_code == 409
    finally:
        engine.dispose()


def test_protected_route_rejects_missing_and_invalid_tokens():
    client, engine = create_client()
    secret = SecretStr("test-secret-key-with-at-least-32-bytes")
    try:
        with (
            patch.object(settings, "AUTH_MODE", "jwt"),
            patch.object(settings, "JWT_SECRET_KEY", secret),
        ):
            assert client.get("/protected").status_code == 401
            assert client.get(
                "/protected",
                headers={"Authorization": "Bearer invalid-token"},
            ).status_code == 401
    finally:
        engine.dispose()
