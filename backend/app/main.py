import json
import time
import uuid
from typing import Annotated

import cv2
import numpy as np
from fastapi import APIRouter, FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

from backend.vision.image_processor import ImageProcesser
from common.configs.constants import REDIS, StreamConfig
from common.configs.data_schemas import AddedCard, EmbeddingTask

app = FastAPI()
router = APIRouter(prefix="/api")

# Instantiate the stream config globally
stream_config = StreamConfig()


@router.post("/scan")
async def scan_card(image: Annotated[UploadFile, File()]) -> JSONResponse:
    """Receive a card photo from the frontend, detect contours, crop cards, and push to Redis."""
    contents = await image.read()
    np_arr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        return JSONResponse(status_code=400, content={"error": "Invalid image"})

    crop = ImageProcesser.process_image(frame)
    _, encoded = cv2.imencode(".jpg", crop)

    embedding_task = EmbeddingTask(
        frame_id=str(uuid.uuid4()),
        image_bytes=encoded.tobytes(),
        created_at=time.time(),
    )

    REDIS.xadd(stream_config.stream_name, embedding_task.model_dump(), maxlen=100, approximate=True)
    cv2.imwrite(f"/app/data/crops/{embedding_task.frame_id}.jpg", crop)

    return JSONResponse(
        status_code=200,
        content={"frame_id": embedding_task.frame_id},
    )


@router.get("/result/{frame_id}")
async def get_scan_result(frame_id: str) -> JSONResponse:
    result = REDIS.get(f"result:{frame_id}")
    print(frame_id)
    if result:
        REDIS.delete(f"result:{frame_id}")
        return JSONResponse(status_code=200, content=json.loads(result))

    return JSONResponse(status_code=202, content={"status": "processing"})


@router.post("/collection/add")
async def add_cards_to_collection(cards: list[AddedCard]) -> JSONResponse:
    print(f"Received {len(cards)} cards for database insertion.")
    return JSONResponse(status_code=200, content={"status": "success", "inserted": len(cards)})


app.include_router(router)
