import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete
from app.db.models.strategy import Strategy
from app.schemas.strategy import StrategyCreate, StrategyUpdate

async def get_strategies(session: AsyncSession, user_id: uuid.UUID) -> List[Strategy]:
    result = await session.execute(
        select(Strategy).where((Strategy.user_id == user_id) | (Strategy.is_default == True))
    )
    return result.scalars().all()

async def create_strategy(session: AsyncSession, user_id: uuid.UUID, data: StrategyCreate) -> Strategy:
    strategy = Strategy(
        id=uuid.uuid4(),
        user_id=user_id,
        name=data.name,
        description=data.description,
        is_default=False,
    )
    session.add(strategy)
    await session.commit()
    await session.refresh(strategy)
    return strategy

async def update_strategy(session: AsyncSession, user_id: uuid.UUID, strategy_id: uuid.UUID, data: StrategyUpdate) -> Optional[Strategy]:
    result = await session.execute(
        select(Strategy).where(Strategy.id == strategy_id, Strategy.user_id == user_id)
    )
    strategy = result.scalar_one_or_none()
    if not strategy:
        return None
    if data.name is not None:
        strategy.name = data.name
    if data.description is not None:
        strategy.description = data.description
    await session.commit()
    await session.refresh(strategy)
    return strategy

async def delete_strategy(session: AsyncSession, user_id: uuid.UUID, strategy_id: uuid.UUID) -> bool:
    result = await session.execute(
        select(Strategy).where(Strategy.id == strategy_id, Strategy.user_id == user_id)
    )
    strategy = result.scalar_one_or_none()
    if not strategy:
        return False
    await session.delete(strategy)
    await session.commit()
    return True
