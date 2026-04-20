import time

from pydantic import BaseModel


class EmbeddingTask(BaseModel):
    """Crop Redis Task to process."""

    frame_id: str
    image_bytes: bytes
    created_at: float = time.time()


class InferenceResult(BaseModel):
    """Final embedding inference result format returned to the backend."""

    frame_id: str
    card_number: str | None = None
    card_set: str | None = None
    card_name: str | None = None
    card_language: str | None = None
    card_side: str | None = None
