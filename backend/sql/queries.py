from sqlalchemy import case, delete, func, select, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from common.db.models import Card, Collection
from common.schemas.api import AddedCard, CollectionItemResponse, PaginatedCollection, UpdateCollectionItem


async def bulk_add_cards(db: AsyncSession, cards_data: list[AddedCard]) -> int:
    if not cards_data:
        return 0

    aggregated: dict[tuple, dict] = {}
    for card in cards_data:
        key = (card.id, card.is_foil, card.card_condition)
        if key in aggregated:
            aggregated[key]["quantity"] += card.quantity
        else:
            aggregated[key] = {
                "card_id": card.id,
                "is_foil": card.is_foil,
                "card_condition": card.card_condition,
                "quantity": card.quantity,
            }

    values_payload = list(aggregated.values())
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


async def get_paginated_collection(
    db: AsyncSession,
    limit: int = 100,
    offset: int = 0,
    sort_by: str = "added_at",
    order: str = "desc",
) -> PaginatedCollection:
    total_count = await db.scalar(select(func.count(Collection.collection_id)))

    rarity_weight = case(
        {
            "mythic": 1,
            "rare": 2,
            "uncommon": 3,
            "common": 4,
        },
        value=Card.card_rarity,
        else_=5,
    )

    sort_map = {
        "added_at": Collection.added_at,
        "last_updated": Collection.last_updated,
        "quantity": Collection.quantity,
        "card_name": Card.card_name,
        "card_set": Card.card_set,
        "card_rarity": rarity_weight,
    }

    sort_col = sort_map.get(sort_by, Collection.added_at)
    order_clause = sort_col.desc() if order == "desc" else sort_col.asc()

    stmt = (
        select(Collection, Card)
        .join(Card, Collection.card_id == Card.id)
        .order_by(order_clause)
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)

    items = []
    for collection_row, card_row in result.all():
        mapped_item = CollectionItemResponse(
            collection_id=collection_row.collection_id,
            card_id=collection_row.card_id,
            card_name=card_row.card_name,
            card_set=card_row.card_set,
            card_number=card_row.card_number,
            card_language=card_row.card_language,
            card_rarity=card_row.card_rarity,
            card_image_url=card_row.card_image_url,
            is_foil=collection_row.is_foil,
            card_condition=collection_row.card_condition,
            quantity=collection_row.quantity,
            added_at=collection_row.added_at,
            last_updated=collection_row.last_updated,
        )
        items.append(mapped_item)

    return PaginatedCollection(total_count=total_count or 0, items=items)


async def update_collection_item(db: AsyncSession, collection_id: int, updates: UpdateCollectionItem) -> bool:
    update_data = {k: v for k, v in updates.model_dump(exclude_unset=True).items() if v is not None}

    if not update_data:
        return False

    update_data["last_updated"] = func.now()

    stmt = (
        update(Collection)
        .where(Collection.collection_id == collection_id)
        .values(**update_data)
        .execution_options(synchronize_session=False)
    )
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0


async def delete_collection_item(db: AsyncSession, collection_id: int) -> bool:
    stmt = delete(Collection).where(Collection.collection_id == collection_id)
    result = await db.execute(stmt)
    await db.commit()
    return result.rowcount > 0
