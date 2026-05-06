import datetime
import uuid

from sqlalchemy import Boolean, CheckConstraint, DateTime, Float, ForeignKey, Integer, String, UniqueConstraint
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
    card_rarity: Mapped[str] = mapped_column(String(10), nullable=False)
    card_cmc: Mapped[int] = mapped_column(Integer, nullable=False)
    card_colors: Mapped[str] = mapped_column(String(10), nullable=False)
    card_image_url: Mapped[str] = mapped_column(String(150), nullable=False)

    collections: Mapped[list["Collection"]] = relationship(back_populates="card", cascade="all, delete-orphan")
    prices: Mapped[list["CardPrice"]] = relationship(back_populates="card", cascade="all, delete-orphan")


class Collection(Base):
    """Specific physical inventory owned by the user."""

    __tablename__ = "collection"

    collection_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), nullable=False)
    is_foil: Mapped[bool] = mapped_column(Boolean, default=False)
    card_condition: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    added_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    last_updated: Mapped[datetime.datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.datetime.now(datetime.UTC),
        onupdate=lambda: datetime.datetime.now(datetime.UTC),
    )

    __table_args__ = (
        CheckConstraint("quantity >= 0", name="check_quantity_positive"),
        UniqueConstraint("card_id", "is_foil", "card_condition", name="uq_collection_item"),
    )

    card: Mapped["Card"] = relationship(back_populates="collections")


class CardPrice(Base):
    """Daily price snapshot for a card, sourced from Scryfall."""

    __tablename__ = "card_prices"

    price_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    card_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cards.id"), nullable=False, index=True)
    price_usd: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_usd_foil: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_eur: Mapped[float | None] = mapped_column(Float, nullable=True)
    price_eur_foil: Mapped[float | None] = mapped_column(Float, nullable=True)
    fetched_at: Mapped[datetime.datetime] = mapped_column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))

    card: Mapped["Card"] = relationship(back_populates="prices")
