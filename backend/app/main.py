import tempfile
import time
import uuid
from dataclasses import asdict
from typing import Annotated

import cv2
import numpy as np
import redis
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse

from backend.vision.image_processor import ImageProcesser
from common.configs.data_schemas import CropTask, RedisConfig

r = redis.Redis(**asdict(RedisConfig()))
image_processor = ImageProcesser()

app = FastAPI()


@app.post("/api/scan")
async def scan_card(image: Annotated[UploadFile, File()]) -> JSONResponse:
    """Receive a card photo from the frontend, detect contours, crop cards, and push to Redis."""
    contents = await image.read()
    np_arr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

    if frame is None:
        return JSONResponse(status_code=400, content={"error": "Invalid image"})

    _, contours = image_processor.find_big_contours(frame)

    crops_created = []
    for contour in contours:
        crop = image_processor.crop_warp_image_from_contour(frame, contour)

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp_file:
            cv2.imwrite(tmp_file.name, crop)
            tmp_file.flush()
            tmp_file.seek(0)

        crop_task = CropTask(
            track_id=str(uuid.uuid4()),
            frame_id=str(uuid.uuid4()),
            image_ref=tmp_file.name,
            created_at=time.time(),
        )

        # r.xadd("crop_stream", crop_task.model_dump(), maxlen=100, approximate=True)
        crops_created.append(crop_task.track_id)

    return JSONResponse(
        status_code=200,
        content={
            "cards_found": len(crops_created),
            "track_ids": crops_created,
        },
    )
