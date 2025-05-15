from fastapi import Depends, HTTPException, status, Request
from app.db.models.user import User
import uuid

class DummyUser:
    id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    email = "testuser@example.com"

async def get_current_user(request: Request) -> User:
    # TEST-ONLY BYPASS: Always return a dummy user. Replace with real auth for production.
    return DummyUser()
