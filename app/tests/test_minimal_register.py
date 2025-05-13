import pytest
from fastapi import FastAPI, status
from pydantic import BaseModel, EmailStr
from httpx import AsyncClient, ASGITransport

app = FastAPI()

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    role: str = "user"

@app.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate):
    return {"email": user_in.email, "role": user_in.role}

@pytest.mark.asyncio
async def test_minimal_register():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/register", json={
            "email": "minimal@example.com",
            "password": "TestPassword123!",
            "role": "user"
        })
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["email"] == "minimal@example.com" 