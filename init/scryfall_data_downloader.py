import logging

import ijson
import pandas as pd
import requests

from common.init.constants import ALL_CARDS_JSON, CARDS_METADATA_PARQUET

logger = logging.getLogger(__name__)


def download_bulk_data() -> None:
    """Download the full bulk data JSON from Scryfall if not present."""
    resp = requests.get("https://api.scryfall.com/bulk-data", timeout=60)
    resp.raise_for_status()
    data = resp.json()["data"]
    all_cards_uri = next(item["download_uri"] for item in data if item["type"] == "all_cards")

    with requests.get(all_cards_uri, stream=True, timeout=60) as r:
        r.raise_for_status()
        logger.info("Downloading all_cards.json...")

        downloaded = 0
        last_log_mb = 0

        with ALL_CARDS_JSON.open("wb") as f:
            for chunk in r.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    downloaded_mb = downloaded / (1024 * 1024)
                    if downloaded_mb >= last_log_mb + 200:
                        logger.info("Downloaded %s MB...", int(downloaded_mb))
                        last_log_mb = downloaded_mb

        logger.info("Finished downloading all_cards.json")


def parse_metadata() -> None:
    """Stream and parse the massive JSON file to extract card metadata and URLs."""
    records = []

    with ALL_CARDS_JSON.open("rb") as f:
        cards = ijson.items(f, "item")

        logger.info("Parsing cards from JSON...")
        count = 0

        for card in cards:
            count += 1
            if count % 50000 == 0:
                logger.info("Parsed %s cards...", count)
            if card.get("digital") or card.get("image_status") in ("missing", "placeholder"):
                continue
            if "paper" not in card.get("games", []):
                continue
            if card.get("layout") == "art_series":
                continue

            # Core fields
            card_id = card.get("id", "")
            card_lang = card.get("lang", "en")
            card_set = card.get("set", "")

            original_name = card.get("name", "")

            card_number = card.get("collector_number", "")
            rarity = card.get("rarity", "")
            cmc = float(card.get("cmc", 0.0))
            set_name = card.get("set_name", "")

            # Convert colors list into a comma-separated string
            colors_list = card.get("colors", [])
            colors = ",".join(colors_list) if isinstance(colors_list, list) else str(colors_list)

            base_record = {
                "id": card_id,
                "card_name": original_name,
                "card_set": card_set,
                "card_language": card_lang,
                "card_number": card_number,
                "card_rarity": rarity,
                "card_cmc": cmc,
                "card_set_name": set_name,
                "card_colors": colors,
            }

            layout = card.get("layout")
            if layout in ("modal_dfc", "transform", "reversible"):
                faces = card.get("card_faces", [])
                sides = ["front", "rear"]
                for i, face_obj in enumerate(faces):
                    side = sides[i] if i < len(sides) else f"face{i}"
                    img_uri = face_obj.get("image_uris", {}).get("border_crop")
                    if img_uri:
                        face_record = base_record.copy()
                        face_record["face"] = side
                        face_record["card_image_url"] = img_uri
                        records.append(face_record)
            else:
                img_uri = card.get("image_uris", {}).get("border_crop")
                if img_uri:
                    base_record["face"] = "normal"
                    base_record["card_image_url"] = img_uri
                    records.append(base_record)

    logger.info("Finished parsing. Saving %s records to parquet...", len(records))
    pd.DataFrame(records).to_parquet(CARDS_METADATA_PARQUET, index=False)
    logger.info("Successfully saved parquet metadata.")
