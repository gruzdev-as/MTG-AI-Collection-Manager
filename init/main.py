import logging
import shutil

import gdown
from huggingface_hub import snapshot_download

from common.init.constants import (
    CLIP_MODEL_NAME,
    CROP_DATA_PATH,
    HNSW_FILES_LINK,
    HNSWL_DATA_PATH,
    MODEL_DATA_PATH,
    SCRYFALL_DATA_PATH,
)
from init.populate_cards import populate_cards
from init.scryfall_data_downloader import download_bulk_data, parse_metadata

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


def create_volume_dirs() -> None:
    logger.info("Creating necessary directories")
    MODEL_DATA_PATH.mkdir(parents=True, exist_ok=True)
    HNSWL_DATA_PATH.mkdir(parents=True, exist_ok=True)
    SCRYFALL_DATA_PATH.mkdir(parents=True, exist_ok=True)
    CROP_DATA_PATH.mkdir(parents=True, exist_ok=True)
    logger.info("Done creating directories")


def download_models() -> None:
    logger.info("Downloading models directly from HuggingFace Hub. It may take a while...")
    snapshot_download(
        repo_id=CLIP_MODEL_NAME,
        local_dir=MODEL_DATA_PATH,
        ignore_patterns=["*.msgpack", "*.h5", "*.ot", "*.flax"],
        cache_dir="tmp/hf_cache",
    )
    shutil.rmtree("tmp/hf_cache")
    logger.info("Done downloading models")


def populate_card_metadata() -> None:
    download_bulk_data()
    parse_metadata()
    populate_cards()


def download_hnsw_index() -> None:
    logger.info("Downloading HNSW index from Google Drive...")
    gdown.download_folder(
        HNSW_FILES_LINK,
        output=str(HNSWL_DATA_PATH),
        quiet=True,
    )
    logger.info("Done downloading HNSW index.")


def main() -> None:
    logger.info("Starting init service data verification...")
    create_volume_dirs()
    if not any(MODEL_DATA_PATH.iterdir()):
        logger.info("Model data not found. Downloading models...")
        download_models()
    logger.info("Model data found.")
    if not any(SCRYFALL_DATA_PATH.iterdir()):
        logger.info("Scryfall data not found. Populating card metadata...")
        populate_card_metadata()
    logger.info("Scryfall data found.")
    if not any(HNSWL_DATA_PATH.iterdir()):
        logger.info("HNSW index not found. Downloading...")
        download_hnsw_index()
    logger.info("HNSW index found.")
    logger.info("Init service successfully verified all required data.")


if __name__ == "__main__":
    main()
