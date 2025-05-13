from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime

class TastyTradeAccountCreate(BaseModel):
    tasty_username: str = Field(..., max_length=255)
    tasty_password: str = Field(..., min_length=1)

class TastyTradeAccountRead(BaseModel):
    id: UUID
    tasty_username: str
    created_at: datetime
    updated_at: datetime

class TastyTradeAccountDelete(BaseModel):
    id: UUID
