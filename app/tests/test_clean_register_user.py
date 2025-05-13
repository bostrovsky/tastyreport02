import pytest
from fastapi import FastAPI, status, Depends
# from pydantic import BaseModel, EmailStr
from app.schemas.user import UserCreate
from app.db.session import get_db
from sqlalchemy.ext.asyncio import AsyncSession
from httpx import AsyncClient, ASGITransport

app = FastAPI()

# class UserCreate(BaseModel):
#     email: EmailStr
#     password: str
#     role: str = "user"

# @app.post("/register-user", status_code=status.HTTP_201_CREATED)
# async def register_user(user_in: UserCreate):
#     return {"email": user_in.email, "role": user_in.role}

@app.post("/register-user", status_code=status.HTTP_201_CREATED)
async def register_user(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    return {"email": user_in.email, "role": user_in.role}

@pytest.mark.asyncio
async def test_clean_register_user():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/register-user", json={
            "email": "cleanuser@example.com",
            "password": "TestPassword123!",
            "role": "user"
        })
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["email"] == "cleanuser@example.com"
