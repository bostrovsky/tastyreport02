from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime
import uuid

class UserBase(BaseModel):
    email: EmailStr
    role: str = "user"
    is_active: bool = True

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: uuid.UUID
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class UserInDB(UserRead):
    hashed_password: str
