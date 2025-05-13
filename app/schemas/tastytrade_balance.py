from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class TastyTradeBalanceRead(BaseModel):
    id: UUID
    account_id: UUID
    user_id: UUID
    cash: float | None = None
    long_equity_value: float | None = None
    short_equity_value: float | None = None
    net_liquidating_value: float | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
