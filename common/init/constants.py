from pathlib import Path

# Model data
MODEL_DATA_PATH = Path("data/CLIP")
CLIP_MODEL_NAME = "openai/clip-vit-large-patch14-336"

# HNSW lib data
HNSWL_DATA_PATH = Path("data/hnsw")
HNSW_FILES_LINK = "https://drive.google.com/drive/folders/1FNOtY4-KcdIrOxSsqdGszScTwIKx8Tkk?usp=sharing"
INDEX_FILE = HNSWL_DATA_PATH / "hnsw_index_cos.bin"
MAPPING_FILE = HNSWL_DATA_PATH / "image_metadata.json"

# Card data
SCRYFALL_DATA_PATH = Path("data/scryfall")
ALL_CARDS_JSON = SCRYFALL_DATA_PATH / "all_cards.json"
CARDS_METADATA_PARQUET = SCRYFALL_DATA_PATH / "cards_metadata.parquet"

# Crop data
CROP_DATA_PATH = Path("data/crops")
