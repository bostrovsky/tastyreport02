import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Float, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.user import Base

class TastyTradeTransaction(Base):
    __tablename__ = "tastytrade_transactions"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tastytrade_accounts.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    transaction_type: Mapped[str] = mapped_column(String(64), nullable=False)
    symbol: Mapped[str] = mapped_column(String(64), nullable=True)
    quantity: Mapped[int] = mapped_column(Integer, nullable=True)
    price: Mapped[float] = mapped_column(Float, nullable=True)
    amount: Mapped[float] = mapped_column(Float, nullable=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
