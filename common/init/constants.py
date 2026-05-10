import os
from pathlib import Path

# Model data
MODEL_PATH = Path(os.getenv("MODEL_PATH", ""))
MODEL_NAME = os.getenv("MODEL_NAME", "")

# HNSW lib data
HNSW_PATH = Path(os.getenv("HNSWL_DATA_PATH", ""))
HNSW_FILES_LINK = os.getenv("HNSW_FILES_LINK", "")
INDEX_FILE = HNSW_PATH / os.getenv("HNSW_INDEX_NAME", "")
MAPPING_FILE = HNSW_PATH / os.getenv("HNSW_JSON_NAME", "")

# Card data
SCRYFALL_DATA_PATH = Path(os.getenv("SCRYFALL_DATA_PATH", ""))
ALL_CARDS_JSON = SCRYFALL_DATA_PATH / "all_cards.json"
CARDS_METADATA_PARQUET = SCRYFALL_DATA_PATH / "cards_metadata.parquet"

# Crop data
CROP_DATA_PATH = Path(os.getenv("CROP_DATA_PATH", ""))
