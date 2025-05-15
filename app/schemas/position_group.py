from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime
from typing import Optional, List

class PositionGroupTransactionRead(BaseModel):
    id: UUID
    group_id: UUID
    transaction_id: UUID
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class PositionGroupRead(BaseModel):
    id: UUID
    user_id: UUID
    account_id: UUID
    strategy_id: Optional[UUID] = None
    name: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    transaction_ids: List[UUID]
    model_config = ConfigDict(from_attributes=True)

class PositionGroupCreate(BaseModel):
    account_id: UUID
    strategy_id: Optional[UUID] = None
    name: Optional[str] = None
    transaction_ids: List[UUID]

class PositionGroupUpdate(BaseModel):
    strategy_id: Optional[UUID] = None
    name: Optional[str] = None
    transaction_ids: Optional[List[UUID]] = None
