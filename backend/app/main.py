import tempfile
import time
import uuid
from typing import Annotated

import cv2
import numpy as np
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

from common.configs.constants import REDIS
from common.configs.data_schemas import EmbeddingTask

app = FastAPI()


@app.post("/api/scan")
async def scan_card(image: Annotated[UploadFile, File()]) -> JSONResponse:
    """Receive a card photo from the frontend, detect contours, crop cards, and push to Redis."""
    contents = await image.read()
    np_arr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        return JSONResponse(status_code=400, content={"error": "Invalid image"})

    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
        cv2.imwrite(tmp_file.name, frame)
        tmp_file.flush()
        tmp_file.seek(0)

    embedding_task = EmbeddingTask(
        frame_id=str(uuid.uuid4()),
        image_ref=tmp_file.name,
        created_at=time.time(),
    )

    REDIS.xadd("embedding_stream", embedding_task.model_dump(), maxlen=100, approximate=True)

    return JSONResponse(
        status_code=200,
        content={
            "cards_found": 1,
            "current_embedding_task_len": REDIS.xlen("embedding_stream"),
        },
    )
