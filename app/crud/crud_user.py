from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update
from app.db.models.user import User
from app.schemas.user import UserCreate
from app.core.security import get_password_hash
from datetime import datetime, timezone

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalars().first()

async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    hashed_password = get_password_hash(user_in.password)
    db_user = User(
        email=user_in.email,
        hashed_password=hashed_password,
        role=user_in.role,
        is_active=True
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def update_user_last_login(db: AsyncSession, user: User) -> User:
    user.last_login_at = datetime.now(timezone.utc)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
