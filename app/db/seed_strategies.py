import asyncio
import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import async_session_maker
from app.db.models.strategy import Strategy

DEFAULT_STRATEGIES = [
    ("Naked Put", "Sell put option without owning underlying"),
    ("Covered Call", "Sell call option while owning underlying"),
    ("Vertical Spread", "Buy and sell options of same type and expiry, different strikes"),
    ("Straddle", "Buy call and put at same strike and expiry"),
    ("Strangle", "Buy call and put at different strikes, same expiry"),
    ("Iron Condor", "Sell OTM put and call spreads, same expiry"),
    ("Calendar Spread", "Buy and sell options of same strike, different expiries"),
    ("Butterfly", "Three-strike, same expiry, symmetrical position"),
    ("Collar", "Protective put and covered call"),
    ("Naked Call", "Sell call option without owning underlying"),
    ("Synthetic Long", "Long call + short put, same strike/expiry"),
    ("Synthetic Short", "Long put + short call, same strike/expiry"),
]

async def seed_strategies():
    async with async_session_maker() as session:  # type: AsyncSession
        for name, description in DEFAULT_STRATEGIES:
            result = await session.execute(
                select(Strategy).where(Strategy.name == name, Strategy.is_default == True)
            )
            if not result.scalar():
                strategy = Strategy(
                    id=uuid.uuid4(),
                    user_id=None,
                    name=name,
                    description=description,
                    is_default=True,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc),
                )
                session.add(strategy)
        await session.commit()

if __name__ == "__main__":
    asyncio.run(seed_strategies())
