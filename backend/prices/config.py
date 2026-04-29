from dataclasses import dataclass


@dataclass(frozen=True)
class ScryfallConfig:
    """Configuration constants for the Scryfall price sync."""

    collection_url: str = "https://api.scryfall.com/cards/collection"
    batch_size: int = 100
    rate_limit_delay: float = 0.1
    retention_days: int = 90
    stale_threshold_hours: int = 24
    retry_attempts: int = 3
