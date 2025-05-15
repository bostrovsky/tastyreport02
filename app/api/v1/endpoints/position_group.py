from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from uuid import UUID
from app.schemas.position_group import PositionGroupRead, PositionGroupCreate, PositionGroupUpdate
from app.crud.crud_position_group import get_position_groups, create_position_group, update_position_group, delete_position_group
from app.db.session import async_session_maker
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.v1.endpoints.deps import get_current_user

router = APIRouter(prefix="/position-groups", tags=["position_groups"])

async def get_db():
    async with async_session_maker() as session:
        yield session

@router.get("/", response_model=List[PositionGroupRead])
async def list_position_groups(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await get_position_groups(db, current_user.id)

@router.post("/", response_model=PositionGroupRead, status_code=status.HTTP_201_CREATED)
async def create_new_position_group(
    data: PositionGroupCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return await create_position_group(db, current_user.id, data)

@router.patch("/{group_id}", response_model=PositionGroupRead)
async def update_existing_position_group(
    group_id: UUID,
    data: PositionGroupUpdate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    group = await update_position_group(db, current_user.id, group_id, data)
    if not group:
        raise HTTPException(status_code=404, detail="Position group not found or not owned by user")
    return group

@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_position_group(
    group_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    success = await delete_position_group(db, current_user.id, group_id)
    if not success:
        raise HTTPException(status_code=404, detail="Position group not found or not owned by user")
