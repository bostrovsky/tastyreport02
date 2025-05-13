from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class TastyTradePositionRead(BaseModel):
    id: UUID
    account_id: UUID
    user_id: UUID
    symbol: str
    quantity: int
    average_price: float | None = None
    market_value: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
