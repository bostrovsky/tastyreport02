from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings
from typing import AsyncGenerator

engine = create_async_engine(settings.database_uri, echo=False, future=True)
async_session_maker = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session
