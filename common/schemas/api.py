import time
import uuid
from datetime import datetime

from pydantic import BaseModel


class EmbeddingTask(BaseModel):
    """Crop Redis Task to process."""

    frame_id: str
    image_bytes: bytes
    created_at: float = time.time()


class CardMatch(BaseModel):
    """A single card match from the inference engine."""

    id: uuid.UUID
    card_number: str
    card_set: str
    card_name: str
    card_language: str
    is_foil: bool = False


class InferenceResult(BaseModel):
    """Final embedding inference result format returned to the backend."""

    frame_id: str
    matches: list[CardMatch]


class AddedCard(BaseModel):
    """Payload for adding a card to the inventory from the frontend scanner."""

    id: uuid.UUID
    is_foil: bool = False
    card_condition: str = "NM"
    quantity: int = 1


class CollectionItemResponse(BaseModel):
    """Response model for a single item in the user's collection."""

    collection_id: int
    card_id: uuid.UUID
    card_name: str
    card_set: str
    card_number: str
    card_language: str
    card_rarity: str
    is_foil: bool
    card_condition: str
    quantity: int
    added_at: datetime
    last_updated: datetime


class PaginatedCollection(BaseModel):
    """Response model for a paginated view of the user's collection."""

    total_count: int
    items: list[CollectionItemResponse]


class UpdateCollectionItem(BaseModel):
    """Payload for selectively mutating an inventory stack (Quantity or Condition adjustments)."""

    quantity: int | None = None
    card_condition: str | None = None
    is_foil: bool | None = None
