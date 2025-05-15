import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from app.db.models.position_group import PositionGroup
from app.db.models.position_group_transaction import PositionGroupTransaction
from app.schemas.position_group import PositionGroupCreate, PositionGroupUpdate

async def get_position_groups(session: AsyncSession, user_id: uuid.UUID) -> List[PositionGroup]:
    result = await session.execute(
        select(PositionGroup).where(PositionGroup.user_id == user_id)
    )
    return result.scalars().all()

async def create_position_group(session: AsyncSession, user_id: uuid.UUID, data: PositionGroupCreate) -> PositionGroup:
    group = PositionGroup(
        id=uuid.uuid4(),
        user_id=user_id,
        account_id=data.account_id,
        strategy_id=data.strategy_id,
        name=data.name,
    )
    session.add(group)
    await session.flush()
    for tx_id in data.transaction_ids:
        session.add(PositionGroupTransaction(
            id=uuid.uuid4(),
            group_id=group.id,
            transaction_id=tx_id,
        ))
    await session.commit()
    await session.refresh(group)
    return group

async def update_position_group(session: AsyncSession, user_id: uuid.UUID, group_id: uuid.UUID, data: PositionGroupUpdate) -> Optional[PositionGroup]:
    result = await session.execute(
        select(PositionGroup).where(PositionGroup.id == group_id, PositionGroup.user_id == user_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        return None
    if data.strategy_id is not None:
        group.strategy_id = data.strategy_id
    if data.name is not None:
        group.name = data.name
    if data.transaction_ids is not None:
        # Remove existing links
        await session.execute(
            delete(PositionGroupTransaction).where(PositionGroupTransaction.group_id == group_id)
        )
        # Add new links
        for tx_id in data.transaction_ids:
            session.add(PositionGroupTransaction(
                id=uuid.uuid4(),
                group_id=group_id,
                transaction_id=tx_id,
            ))
    await session.commit()
    await session.refresh(group)
    return group

async def delete_position_group(session: AsyncSession, user_id: uuid.UUID, group_id: uuid.UUID) -> bool:
    result = await session.execute(
        select(PositionGroup).where(PositionGroup.id == group_id, PositionGroup.user_id == user_id)
    )
    group = result.scalar_one_or_none()
    if not group:
        return False
    await session.delete(group)
    await session.commit()
    return True
