from apscheduler.schedulers.asyncio import AsyncIOScheduler

from backend.prices.syncer import cleanup_old_prices, sync_all_prices, sync_if_stale
from common.db.session import AsyncSessionLocal


def build_scheduler() -> AsyncIOScheduler:
    """Create and configure the price sync scheduler (does not start it).

    Registers a daily cron job at 04:00 UTC that performs a full Scryfall
    price fetch followed by a 90-day retention cleanup.
    """
    scheduler = AsyncIOScheduler()

    async def _daily_sync() -> None:
        async with AsyncSessionLocal() as db:
            await sync_all_prices(db)
            await cleanup_old_prices(db)

    scheduler.add_job(_daily_sync, "cron", hour=4, minute=0)
    return scheduler


async def start_price_engine() -> AsyncIOScheduler:
    """Start the scheduler and run the startup sync if prices are stale."""
    scheduler = build_scheduler()
    scheduler.start()

    async with AsyncSessionLocal() as db:
        await sync_if_stale(db)

    return scheduler
