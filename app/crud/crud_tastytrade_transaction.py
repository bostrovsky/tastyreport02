import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from app.db.models.tastytrade_transaction import TastyTradeTransaction
from typing import List
from datetime import datetime

async def upsert_transaction(db: AsyncSession, account_id: uuid.UUID, user_id: uuid.UUID, data: dict) -> TastyTradeTransaction:
    stmt = select(TastyTradeTransaction).where(
        TastyTradeTransaction.account_id == account_id,
        TastyTradeTransaction.user_id == user_id,
        TastyTradeTransaction.symbol == data.get("symbol"),
        TastyTradeTransaction.transaction_type == data["transaction_type"],
        TastyTradeTransaction.date == data.get("date")
    )
    result = await db.execute(stmt)
    transaction = result.scalars().first()
    if transaction:
        for k, v in data.items():
            setattr(transaction, k, v)
    else:
        transaction = TastyTradeTransaction(account_id=account_id, user_id=user_id, **data)
        db.add(transaction)
    await db.commit()
    await db.refresh(transaction)
    return transaction

async def get_transactions_by_account(db: AsyncSession, account_id: uuid.UUID) -> List[TastyTradeTransaction]:
    stmt = select(TastyTradeTransaction).where(TastyTradeTransaction.account_id == account_id)
    result = await db.execute(stmt)
    return result.scalars().all()

async def delete_transactions_by_account(db: AsyncSession, account_id: uuid.UUID) -> None:
    await db.execute(delete(TastyTradeTransaction).where(TastyTradeTransaction.account_id == account_id))
    await db.commit()
