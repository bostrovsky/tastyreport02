from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional

class StrategyRead(BaseModel):
    id: UUID
    user_id: Optional[UUID] = None
    name: str
    description: Optional[str] = None
    is_default: bool
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class StrategyCreate(BaseModel):
    name: str
    description: Optional[str] = None

class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
