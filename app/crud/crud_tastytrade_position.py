import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from app.db.models.tastytrade_position import TastyTradePosition
from typing import List
from datetime import datetime

async def upsert_position(db: AsyncSession, account_id: uuid.UUID, user_id: uuid.UUID, data: dict) -> TastyTradePosition:
    stmt = select(TastyTradePosition).where(
        TastyTradePosition.account_id == account_id,
        TastyTradePosition.user_id == user_id,
        TastyTradePosition.symbol == data["symbol"],
        TastyTradePosition.created_at == data.get("created_at")
    )
    result = await db.execute(stmt)
    position = result.scalars().first()
    if position:
        for k, v in data.items():
            setattr(position, k, v)
    else:
        position = TastyTradePosition(account_id=account_id, user_id=user_id, **data)
        db.add(position)
    await db.commit()
    await db.refresh(position)
    return position

async def get_positions_by_account(db: AsyncSession, account_id: uuid.UUID) -> List[TastyTradePosition]:
    stmt = select(TastyTradePosition).where(TastyTradePosition.account_id == account_id)
    result = await db.execute(stmt)
    return result.scalars().all()

async def delete_positions_by_account(db: AsyncSession, account_id: uuid.UUID) -> None:
    await db.execute(delete(TastyTradePosition).where(TastyTradePosition.account_id == account_id))
    await db.commit()
