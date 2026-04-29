from typing import Any

from sqlalchemy import Select, case, delete, func, select, true, update
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased
from sqlalchemy.sql.elements import ColumnElement

from common.db.models import Card, CardPrice, Collection
from common.schemas.api import AddedCard, CollectionItemResponse, PaginatedCollection, UpdateCollectionItem


def _aggregate_cards_data(cards_data: list[AddedCard]) -> list[dict[str, Any]]:
    """Aggregate identical cards before bulk inserting to avoid redundant rows."""
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
    return list(aggregated.values())


def _get_latest_price_subquery() -> Select:
    """Return a lateral subquery that fetches the most recent price for a card."""
    price_alias = aliased(CardPrice)
    return (
        select(price_alias)
        .where(price_alias.card_id == Card.id)
        .order_by(price_alias.fetched_at.desc())
        .limit(1)
        .correlate(Card)
        .lateral()
    )


def _get_sorting_clause(sort_by: str, order: str, latest_price_subq: Select) -> ColumnElement:
    """Construct the ORDER BY clause based on user input."""
    rarity_weight = case(
        {"mythic": 1, "rare": 2, "uncommon": 3, "common": 4},
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
        "price_usd": func.coalesce(latest_price_subq.c.price_usd, 0.0),
        "price_eur": func.coalesce(latest_price_subq.c.price_eur, 0.0),
    }

    sort_col = sort_map.get(sort_by, Collection.added_at)
    return sort_col.desc() if order == "desc" else sort_col.asc()


async def _get_total_portfolio_value(db: AsyncSession, latest_price_subq: Select) -> tuple[float, float]:
    """Calculate the total USD and EUR value of the entire collection."""
    total_val_stmt = (
        select(
            func.sum(
                Collection.quantity
                * case(
                    (Collection.is_foil, latest_price_subq.c.price_usd_foil),
                    else_=latest_price_subq.c.price_usd,
                ),
            ).label("total_usd"),
            func.sum(
                Collection.quantity
                * case(
                    (Collection.is_foil, latest_price_subq.c.price_eur_foil),
                    else_=latest_price_subq.c.price_eur,
                ),
            ).label("total_eur"),
        )
        .select_from(Collection)
        .join(Card, Collection.card_id == Card.id)
        .outerjoin(latest_price_subq, true())
    )
    val_result = await db.execute(total_val_stmt)
    total_usd, total_eur = val_result.first()
    return total_usd or 0.0, total_eur or 0.0


async def bulk_add_cards(db: AsyncSession, cards_data: list[AddedCard]) -> int:
    if not cards_data:
        return 0

    values_payload = _aggregate_cards_data(cards_data)
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
    latest_price_subq = _get_latest_price_subquery()
    order_clause = _get_sorting_clause(sort_by, order, latest_price_subq)

    stmt = (
        select(
            Collection,
            Card,
            latest_price_subq.c.price_usd,
            latest_price_subq.c.price_usd_foil,
            latest_price_subq.c.price_eur,
            latest_price_subq.c.price_eur_foil,
        )
        .join(Card, Collection.card_id == Card.id)
        .outerjoin(latest_price_subq, true())
        .order_by(order_clause)
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(stmt)

    total_usd, total_eur = await _get_total_portfolio_value(db, latest_price_subq)

    items = [
        CollectionItemResponse(
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
            price_usd=p_usd,
            price_usd_foil=p_usd_foil,
            price_eur=p_eur,
            price_eur_foil=p_eur_foil,
        )
        for collection_row, card_row, p_usd, p_usd_foil, p_eur, p_eur_foil in result.all()
    ]

    return PaginatedCollection(
        total_count=total_count or 0,
        total_value_usd=total_usd,
        total_value_eur=total_eur,
        items=items,
    )


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
