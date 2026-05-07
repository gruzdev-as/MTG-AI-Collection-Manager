import asyncio
import datetime
from collections.abc import Generator
from typing import TYPE_CHECKING, Any, cast
from uuid import UUID

import httpx
from httpcore import TimeoutException
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.prices.config import ScryfallConfig
from common.db.models import Card, CardPrice, Collection

if TYPE_CHECKING:
    from sqlalchemy.engine import CursorResult

cfg = ScryfallConfig()


def _to_float(value: str | None) -> float | None:
    try:
        return float(value) if value is not None else None
    except (ValueError, TypeError):
        return None


def _batched(lst: list[UUID], size: int) -> Generator:
    for i in range(0, len(lst), size):
        yield lst[i : i + size]


def _form_card_data(card_data: dict, price_data: dict, fetch_time: datetime.datetime) -> CardPrice:
    return CardPrice(
        card_id=card_data["id"],
        price_usd=_to_float(price_data.get("usd")),
        price_usd_foil=_to_float(price_data.get("usd_foil")),
        price_eur=_to_float(price_data.get("eur")),
        price_eur_foil=_to_float(price_data.get("eur_foil")),
        fetched_at=fetch_time,
    )


async def sync_all_prices(db: AsyncSession) -> int:
    """Fetch today's prices from Scryfall for cards the user actually owns.

    Only syncs card IDs present in the collection table — not the entire catalog.
    Inserts one CardPrice row per owned card. Returns the number of rows inserted.
    """
    owned_card_id_query = select(Card.id).where(Card.id.in_(select(Collection.card_id).distinct()))
    card_id: list[UUID] = list(await db.scalars(owned_card_id_query))

    if not card_id:
        print("Price sync: collection is empty, nothing to fetch.")
        return 0

    batches = list(_batched(card_id, cfg.batch_size))
    print(f"Price sync: {len(card_id)} cards → {len(batches)} batches of {cfg.batch_size}.")

    new_rows: list[CardPrice] = []
    fetch_time = datetime.datetime.now(datetime.UTC)

    async with httpx.AsyncClient(timeout=30.0) as client:
        for idx, batch in enumerate(batches, start=1):
            payload = {"identifiers": [{"id": str(card_id)} for card_id in batch]}
            success = False
            attempt = 0
            while not success and attempt < cfg.retry_attempts:
                try:
                    resp = await client.post(cfg.collection_url, json=payload)
                    resp.raise_for_status()

                    for card_data in resp.json().get("data", []):
                        price_data = card_data.get("prices", {})
                        new_rows.append(_form_card_data(card_data, price_data, fetch_time))

                    print(f"Price sync: batch {idx}/{len(batches)} OK.")
                    success = True
                except TimeoutException:
                    attempt += 1
                    wait = attempt * 2.0
                    print(f"Price sync: batch {idx}/{len(batches)} attempt {attempt} failed, retrying in {wait}s.")
                    await asyncio.sleep(wait)
            if not success:
                print(f"Price sync: batch {idx}/{len(batches)} failed after {cfg.retry_attempts} attempts.")
            if idx < len(batches):
                await asyncio.sleep(cfg.rate_limit_delay)

    if new_rows:
        db.add_all(new_rows)
        await db.commit()

    print(f"Price sync: inserted {len(new_rows)} price records.")
    return len(new_rows)


async def sync_if_stale(db: AsyncSession) -> int:
    """Run sync only if the last snapshot is >= X hours old (or never run).

    Called on application startup to avoid hammering Scryfall after quick restarts.
    """
    last_sync: datetime.datetime | None = await db.scalar(
        select(CardPrice.fetched_at).order_by(CardPrice.fetched_at.desc()).limit(1),
    )

    if last_sync is None:
        print("Price sync: no price data found. Starting sync.")
        return await sync_all_prices(db)

    if last_sync.tzinfo is None:
        last_sync = last_sync.replace(tzinfo=datetime.UTC)

    age = datetime.datetime.now(datetime.UTC) - last_sync
    if age < datetime.timedelta(hours=cfg.stale_threshold_hours):
        print(f"Price sync skipped on startup: last sync was {age.total_seconds() / 3600:.1f} hours ago.")
        return 0

    print(f"Price sync: starting startup sync (last sync >= {cfg.stale_threshold_hours} hours ago.")
    return await sync_all_prices(db)


async def cleanup_old_prices(db: AsyncSession) -> int:
    """Delete price snapshots older than RETENTION_DAYS (90 days).

    Called after each daily sync to keep the history table bounded.
    """
    cutoff = datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=cfg.retention_days)
    stmt = delete(CardPrice).where(CardPrice.fetched_at < cutoff)
    result = cast("CursorResult[Any]", await db.execute(stmt))
    await db.commit()

    if result.rowcount:
        print(f"Price cleanup: removed {result.rowcount} records older than {cfg.retention_days} days.")
    return result.rowcount
