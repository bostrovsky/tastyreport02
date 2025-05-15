from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.schemas.strategy import StrategyRead, StrategyCreate, StrategyUpdate
from app.crud.crud_strategy import get_strategies, create_strategy, update_strategy, delete_strategy
from app.db.session import async_session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.endpoints.deps import get_current_user

router = APIRouter(prefix="/strategies", tags=["strategies"])

async def get_db():
    async with async_session_maker() as session:
        yield session

@router.get("/", response_model=List[StrategyRead])
async def list_strategies(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_strategies(db, current_user.id)

@router.post("/", response_model=StrategyRead, status_code=status.HTTP_201_CREATED)
async def create_new_strategy(
    data: StrategyCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await create_strategy(db, current_user.id, data)

@router.patch("/{strategy_id}", response_model=StrategyRead)
async def update_existing_strategy(
    strategy_id: UUID,
    data: StrategyUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    strategy = await update_strategy(db, current_user.id, strategy_id, data)
    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found or not owned by user")
    return strategy

@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_strategy(
    strategy_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    success = await delete_strategy(db, current_user.id, strategy_id)
    if not success:
        raise HTTPException(status_code=404, detail="Strategy not found or not owned by user")
