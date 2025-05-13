import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.main import app
from app.db.session import async_session_maker
import asyncio

import os
os.environ["TESTING"] = "1"

@pytest.mark.asyncio
async def test_register_and_login_and_me():
    # Cleanup: delete all users before running the test
    async with async_session_maker() as session:
        await session.execute(text("DELETE FROM users"))
        await session.commit()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        # Register
        resp = await ac.post("/api/v1/auth/register-user", json={
            "email": "testuser@example.com",
            "password": "TestPassword123!",
            "role": "user"
        })
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["email"] == "testuser@example.com"
        assert "id" in data

        # Duplicate registration
        resp2 = await ac.post("/api/v1/auth/register-user", json={
            "email": "testuser@example.com",
            "password": "TestPassword123!",
            "role": "user"
        })
        assert resp2.status_code == 400

        # Login
        resp3 = await ac.post("/api/v1/auth/login", json={
            "email": "testuser@example.com",
            "password": "TestPassword123!"
        })
        assert resp3.status_code == 200, resp3.text
        tokens = resp3.json()
        assert "access_token" in tokens
        assert "refresh_token" in tokens

        # /me with valid token
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}
        resp4 = await ac.get("/api/v1/auth/me", headers=headers)
        assert resp4.status_code == 200
        me = resp4.json()
        assert me["email"] == "testuser@example.com"

        # /me with invalid token
        resp5 = await ac.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalidtoken"})
        assert resp5.status_code == 401

        # /me with no token
        resp6 = await ac.get("/api/v1/auth/me")
        assert resp6.status_code == 401

        # Refresh token
        resp7 = await ac.post("/api/v1/auth/refresh-token", json={"refresh_token": tokens["refresh_token"]})
        assert resp7.status_code == 200
        new_tokens = resp7.json()
        assert "access_token" in new_tokens
        assert "refresh_token" in new_tokens

        # Logout (no-op)
        resp8 = await ac.post("/api/v1/auth/logout")
        assert resp8.status_code == 204
