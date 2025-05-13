import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from app.db.models.tastytrade_account import TastyTradeAccount
from app.core.encryption import encrypt, decrypt
from app.schemas.tastytrade_account import TastyTradeAccountCreate
from typing import List, Optional

async def create_tastytrade_account(db: AsyncSession, user_id: uuid.UUID, account_in: TastyTradeAccountCreate) -> TastyTradeAccount:
    encrypted_password = encrypt(account_in.tasty_password)
    account = TastyTradeAccount(
        user_id=user_id,
        tasty_username=account_in.tasty_username,
        tasty_password_encrypted=encrypted_password,
    )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account

async def get_tastytrade_accounts_by_user(db: AsyncSession, user_id: uuid.UUID) -> List[TastyTradeAccount]:
    result = await db.execute(select(TastyTradeAccount).where(TastyTradeAccount.user_id == user_id))
    return result.scalars().all()

async def get_tastytrade_account_by_id(db: AsyncSession, account_id: uuid.UUID) -> Optional[TastyTradeAccount]:
    result = await db.execute(select(TastyTradeAccount).where(TastyTradeAccount.id == account_id))
    return result.scalars().first()

async def delete_tastytrade_account(db: AsyncSession, account_id: uuid.UUID) -> None:
    await db.execute(delete(TastyTradeAccount).where(TastyTradeAccount.id == account_id))
    await db.commit()
