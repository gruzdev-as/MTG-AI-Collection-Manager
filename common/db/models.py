import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class Card(Base):
    """Database model for MTG cards in the collection."""

    __tablename__ = "cards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    card_name: Mapped[str | None] = mapped_column(String(255))
    card_number: Mapped[int | None] = mapped_column(Integer)
    card_set: Mapped[str | None] = mapped_column(String(50))
    card_language: Mapped[str | None] = mapped_column(String(50))
    is_foil: Mapped[bool] = mapped_column(Boolean, default=False)
    card_condition: Mapped[str | None] = mapped_column(String(50))

    scanned_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
