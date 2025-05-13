import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from app.db.models.tastytrade_balance import TastyTradeBalance
from typing import Optional
from datetime import datetime

async def upsert_balance(db: AsyncSession, account_id: uuid.UUID, user_id: uuid.UUID, data: dict) -> TastyTradeBalance:
    # Upsert by account_id, user_id, created_at (one per sync)
    stmt = select(TastyTradeBalance).where(
        TastyTradeBalance.account_id == account_id,
        TastyTradeBalance.user_id == user_id,
        TastyTradeBalance.created_at == data.get("created_at")
    )
    result = await db.execute(stmt)
    balance = result.scalars().first()
    if balance:
        for k, v in data.items():
            setattr(balance, k, v)
    else:
        balance = TastyTradeBalance(account_id=account_id, user_id=user_id, **data)
        db.add(balance)
    await db.commit()
    await db.refresh(balance)
    return balance

async def get_latest_balance(db: AsyncSession, account_id: uuid.UUID) -> Optional[TastyTradeBalance]:
    stmt = select(TastyTradeBalance).where(TastyTradeBalance.account_id == account_id).order_by(TastyTradeBalance.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().first()

async def delete_balances_by_account(db: AsyncSession, account_id: uuid.UUID) -> None:
    await db.execute(delete(TastyTradeBalance).where(TastyTradeBalance.account_id == account_id))
    await db.commit()
