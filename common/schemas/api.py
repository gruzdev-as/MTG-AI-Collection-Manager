import time
import uuid

from pydantic import BaseModel


class EmbeddingTask(BaseModel):
    """Crop Redis Task to process."""

    frame_id: str
    image_bytes: bytes
    created_at: float = time.time()


class InferenceResult(BaseModel):
    """Final embedding inference result format returned to the backend."""

    frame_id: str
    id: uuid.UUID
    card_number: int
    card_set: str
    card_name: str
    card_language: str
    is_foil: bool = False


class AddedCard(BaseModel):
    """Payload for adding a card to the inventory from the frontend scanner."""

    # The exact Scryfall UUID resolved by the HNSW search
    id: uuid.UUID

    # Inventory specific mutable properties
    is_foil: bool = False
    card_condition: str = "NM"
    quantity: int = 1
