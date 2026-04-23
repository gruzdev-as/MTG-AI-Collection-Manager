from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from common.db.models import Collection
from common.schemas.api import AddedCard


async def bulk_add_cards(db: AsyncSession, cards_data: list[AddedCard]) -> int:
    if not cards_data:
        return 0

    values_payload = [
        {
            "card_id": card.id,
            "is_foil": card.is_foil,
            "card_condition": card.card_condition,
            "quantity": card.quantity,
        }
        for card in cards_data
    ]

    collection_insert_stmt = insert(Collection).values(values_payload)

    collection_upsert_stmt = collection_insert_stmt.on_conflict_do_update(
        index_elements=["card_id", "is_foil", "card_condition"],
        set_={
            "quantity": Collection.quantity + collection_insert_stmt.excluded.quantity,
            "last_updated": func.now(),
        },
    )

    await db.execute(collection_upsert_stmt)
    await db.commit()

    return len(cards_data)
