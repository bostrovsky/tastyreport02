import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.user import Base

class TastyTradeBalance(Base):
    __tablename__ = "tastytrade_balances"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tastytrade_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    cash: Mapped[float] = mapped_column(Float, nullable=True)
    long_equity_value: Mapped[float] = mapped_column(Float, nullable=True)
    short_equity_value: Mapped[float] = mapped_column(Float, nullable=True)
    net_liquidating_value: Mapped[float] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
