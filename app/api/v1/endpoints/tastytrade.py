from fastapi import APIRouter, Depends, HTTPException, status, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from app.db.session import get_db
from app.api.v1.deps import get_current_active_user
from app.db.models.user import User
from app.schemas.tastytrade_account import TastyTradeAccountCreate, TastyTradeAccountRead
from app.crud.crud_tastytrade_account import (
    create_tastytrade_account,
    get_tastytrade_accounts_by_user,
    delete_tastytrade_account,
    get_tastytrade_account_by_id,
)
from app.core.encryption import decrypt
from typing import List
import tastytrade
from tastytrade.utils import TastytradeError
from app.crud.crud_tastytrade_balance import upsert_balance, get_latest_balance
from app.crud.crud_tastytrade_position import upsert_position, get_positions_by_account
from app.crud.crud_tastytrade_transaction import upsert_transaction, get_transactions_by_account
from datetime import datetime, timezone
from sqlalchemy import select
from app.schemas.tastytrade_balance import TastyTradeBalanceRead
from app.schemas.tastytrade_position import TastyTradePositionRead
from app.schemas.tastytrade_transaction import TastyTradeTransactionRead
from app.db.models.tastytrade_balance import TastyTradeBalance
from app.db.models.tastytrade_position import TastyTradePosition
from app.db.models.tastytrade_transaction import TastyTradeTransaction

router = APIRouter(prefix="/tastytrade/accounts", tags=["tastytrade"])

@router.post("/", response_model=TastyTradeAccountRead, status_code=status.HTTP_201_CREATED)
async def add_tastytrade_account(
    account_in: TastyTradeAccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    account = await create_tastytrade_account(db, current_user.id, account_in)
    return account

@router.get("/", response_model=List[TastyTradeAccountRead])
async def list_tastytrade_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    accounts = await get_tastytrade_accounts_by_user(db, current_user.id)
    return accounts

@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tastytrade_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    account = await get_tastytrade_account_by_id(db, account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Account not found")
    await delete_tastytrade_account(db, account_id)
    return None

@router.post("/sync/{account_id}", status_code=status.HTTP_202_ACCEPTED)
async def sync_tastytrade_account(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    account = await get_tastytrade_account_by_id(db, account_id)
    if not account or account.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Account not found")
    try:
        username = account.tasty_username
        password = decrypt(account.tasty_password_encrypted)
        session = tastytrade.Session(username, password)
        accounts = await tastytrade.Account.a_get(session)
        if not accounts:
            raise HTTPException(status_code=404, detail="No TastyTrade accounts found")
        tasty_account = accounts[0]
        # --- Balances ---
        balances = await tasty_account.a_get_balances(session)
        balance_data = {
            "cash": getattr(balances, "cash", None),
            "long_equity_value": getattr(balances, "long_equity_value", None),
            "short_equity_value": getattr(balances, "short_equity_value", None),
            "net_liquidating_value": getattr(balances, "net_liquidating_value", None),
            "created_at": datetime.now(timezone.utc),
        }
        await upsert_balance(db, account_id, current_user.id, balance_data)
        # --- Positions ---
        positions = await tasty_account.a_get_positions(session)
        pos_list = []
        for pos in positions:
            pos_data = {
                "symbol": getattr(pos, "symbol", None),
                "quantity": getattr(pos, "quantity", None),
                "average_price": getattr(pos, "average_price", None),
                "market_value": getattr(pos, "market_value", None),
                "created_at": datetime.now(timezone.utc),
            }
            await upsert_position(db, account_id, current_user.id, pos_data)
            pos_list.append(pos_data)
        # --- Transactions ---
        transactions = await tasty_account.a_get_history(session)
        txn_list = []
        for txn in transactions:
            txn_data = {
                "transaction_type": getattr(txn, "transaction_type", None),
                "symbol": getattr(txn, "symbol", None),
                "quantity": getattr(txn, "quantity", None),
                "price": getattr(txn, "price", None),
                "amount": getattr(txn, "amount", None),
                "date": getattr(txn, "date", None),
                "created_at": datetime.now(timezone.utc),
            }
            await upsert_transaction(db, account_id, current_user.id, txn_data)
            txn_list.append(txn_data)
        return {"detail": "Sync successful", "balances": balance_data, "positions": pos_list, "transactions": txn_list}
    except TastytradeError as e:
        if "invalid_credentials" in str(e):
            raise HTTPException(status_code=401, detail="TastyTrade login failed")
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")

@router.get("/{account_id}/balances", response_model=list[TastyTradeBalanceRead])
async def get_balances(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    response: Response = None,
):
    account = await get_tastytrade_account_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this account")
    stmt = (
        select(TastyTradeBalance)
        .where(TastyTradeBalance.account_id == account_id)
        .order_by(TastyTradeBalance.created_at.desc())
    )
    result = await db.execute(stmt)
    all_balances = result.scalars().all()
    response.headers["X-Total-Count"] = str(len(all_balances))
    balances = all_balances[offset:offset+limit]
    return [TastyTradeBalanceRead.model_validate(b) for b in balances]

@router.get("/{account_id}/positions", response_model=list[TastyTradePositionRead])
async def get_positions(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    response: Response = None,
):
    account = await get_tastytrade_account_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this account")
    stmt = (
        select(TastyTradePosition)
        .where(TastyTradePosition.account_id == account_id)
        .order_by(TastyTradePosition.created_at.desc())
    )
    result = await db.execute(stmt)
    all_positions = result.scalars().all()
    response.headers["X-Total-Count"] = str(len(all_positions))
    positions = all_positions[offset:offset+limit]
    return [TastyTradePositionRead.model_validate(p) for p in positions]

@router.get("/{account_id}/transactions", response_model=list[TastyTradeTransactionRead])
async def get_transactions(
    account_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    response: Response = None,
):
    account = await get_tastytrade_account_by_id(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden: You do not own this account")
    stmt = (
        select(TastyTradeTransaction)
        .where(TastyTradeTransaction.account_id == account_id)
        .order_by(TastyTradeTransaction.created_at.desc())
    )
    result = await db.execute(stmt)
    all_transactions = result.scalars().all()
    response.headers["X-Total-Count"] = str(len(all_transactions))
    transactions = all_transactions[offset:offset+limit]
    return [TastyTradeTransactionRead.model_validate(t) for t in transactions]
