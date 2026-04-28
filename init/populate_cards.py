import logging

import pandas as pd
from sqlalchemy import create_engine

from common.db.config import PostgresConfig
from common.db.models import Base, Card
from common.init.constants import SCRYFALL_DATA_PATH

logger = logging.getLogger(__name__)


def populate_cards() -> None:
    parquet_path = SCRYFALL_DATA_PATH / "cards_metadata.parquet"

    logger.info("Reading parquet from %s", parquet_path)
    cards_df = pd.read_parquet(parquet_path).drop(columns=["face"])
    cards_df = cards_df.drop_duplicates(subset=["id"])

    logger.info("Connecting to Postgres to push %s unique cards...", len(cards_df))
    engine = create_engine(PostgresConfig().alt_url)
    Base.metadata.create_all(bind=engine)

    logger.info("Writing cards to database in chunks of %s...", 10000)
    cards_df.to_sql(Card.__tablename__, con=engine, if_exists="append", index=False, chunksize=10000)
    logger.info("Successfully populated cards table.")
