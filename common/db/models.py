import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, CheckConstraint, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Base class for SQLAlchemy models."""


class Card(Base):
    """Database model for MTG cards in the collection."""

    __tablename__ = "cards"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True)
    card_name: Mapped[str] = mapped_column(String(200), nullable=False)
    card_number: Mapped[str] = mapped_column(String(10), nullable=False)
    card_set: Mapped[str] = mapped_column(String(10), nullable=False)
    card_set_name: Mapped[str | None] = mapped_column(String(100))
    card_language: Mapped[str] = mapped_column(String(5), nullable=False)

    collections: Mapped[list["Collection"]] = relationship(back_populates="card", cascade="all, delete-orphan")


class Collection(Base):
    """Specific physical inventory owned by the user."""

    __tablename__ = "collection"

    collection_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), nullable=False)
    is_foil: Mapped[bool] = mapped_column(Boolean, default=False)
    card_condition: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    added_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    last_updated: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="check_quantity_positive"),
        UniqueConstraint("card_id", "is_foil", "card_condition", name="uq_collection_item"),
    )

    card: Mapped["Card"] = relationship(back_populates="collections")
