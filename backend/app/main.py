import json
import time
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Annotated

import cv2
import numpy as np
from fastapi import APIRouter, Depends, FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend import prices
from backend.prices import start_price_engine
from backend.sql import queries
from backend.vision.image_processor import ImageProcesser
from common.db.models import Base
from common.db.session import engine, get_db
from common.redis.client import REDIS
from common.redis.config import StreamConfig
from common.schemas.api import AddedCard, EmbeddingTask, PaginatedCollection, UpdateCollectionItem


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None]:
    """Lifecycle events for the FastAPI application."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    scheduler = await start_price_engine()
    yield
    scheduler.shutdown()


app = FastAPI(lifespan=lifespan)
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

    return JSONResponse(status_code=200, content={"frame_id": embedding_task.frame_id})


@router.get("/result/{frame_id}")
async def get_scan_result(frame_id: str) -> JSONResponse:
    result = REDIS.get(f"result:{frame_id}")
    if result:
        REDIS.delete(f"result:{frame_id}")
        return JSONResponse(status_code=200, content=json.loads(result))
    return JSONResponse(status_code=202, content={"status": "processing"})


@router.post("/collection/add")
async def add_cards_to_collection(cards: list[AddedCard], db: Annotated[AsyncSession, Depends(get_db)]) -> JSONResponse:
    """Commit scanned cards to the persistent database collection."""
    inserted_count = await queries.bulk_add_cards(db, cards)
    print(f"Successfully added {inserted_count} cards to the database.")
    return JSONResponse(status_code=200, content={"status": "success", "inserted": inserted_count})


@router.get("/collection")
async def get_collection(
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "added_at",
    order: str = "desc",
) -> PaginatedCollection:
    """Fetch the active collection mapping with full metadata."""
    return await queries.get_paginated_collection(db, limit, offset, sort_by, order)


@router.put("/collection/{collection_id}")
async def update_collection_item(
    collection_id: int,
    updates: UpdateCollectionItem,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> JSONResponse:
    """Push selective mutations onto an isolated collection stack."""
    success = await queries.update_collection_item(db, collection_id, updates)
    if not success:
        return JSONResponse(status_code=404, content={"error": "Item not found"})
    return JSONResponse(status_code=200, content={"status": "success"})


@router.delete("/collection/{collection_id}")
async def delete_collection_item(collection_id: int, db: Annotated[AsyncSession, Depends(get_db)]) -> JSONResponse:
    """Destroy an inventory stack entirely."""
    success = await queries.delete_collection_item(db, collection_id)
    if not success:
        return JSONResponse(status_code=404, content={"error": "Item not found"})
    return JSONResponse(status_code=200, content={"status": "success"})


@router.post("/prices/sync")
async def trigger_price_sync(db: Annotated[AsyncSession, Depends(get_db)]) -> JSONResponse:
    """Manually trigger a full Scryfall price sync. Useful for testing and on-demand refreshes."""
    synced = await prices.sync_all_prices(db)
    return JSONResponse(status_code=200, content={"status": "success", "synced": synced})


app.include_router(router)
