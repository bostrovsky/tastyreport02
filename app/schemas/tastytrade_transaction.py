from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class TastyTradeTransactionRead(BaseModel):
    id: UUID
    account_id: UUID
    user_id: UUID
    transaction_type: str
    symbol: str | None = None
    quantity: int | None = None
    price: float | None = None
    amount: float | None = None
    date: datetime | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
