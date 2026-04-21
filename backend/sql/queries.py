from sqlalchemy.ext.asyncio import AsyncSession

from common.db.models import Card
from common.schemas.api import AddedCard


async def bulk_add_cards(db: AsyncSession, cards_data: list[AddedCard]) -> int:
    """Bulk insert cards into the database.

    Args:
        db: The asynchronous database session.
        cards_data: List of card schemas from the frontend.

    Returns:
        The number of cards successfully added.

    """
    db_cards = [Card(**card.model_dump()) for card in cards_data]

    db.add_all(db_cards)
    await db.commit()

    return len(db_cards)
