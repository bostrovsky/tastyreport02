import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from app.db.models.user import Base

class TastyTradeAccount(Base):
    __tablename__ = "tastytrade_accounts"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tasty_username: Mapped[str] = mapped_column(String(255), nullable=False)
    tasty_password_encrypted: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=text("now()"), onupdate=datetime.utcnow, nullable=False)
