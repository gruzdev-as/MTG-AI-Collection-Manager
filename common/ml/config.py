import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class InferenceConfig:
    """Configure inference."""

    model_path: Path = Path(os.getenv("MODEL_PATH", ""))


@dataclass(frozen=True)
class HNSWConfig:
    """Configure HNSW index."""

    hnsw_index_path: Path = Path(os.getenv("HNSW_PATH", "")) / os.getenv("HNSW_INDEX_NAME", "")
    hnsw_json_path: Path = Path(os.getenv("HNSW_PATH", "")) / os.getenv("HNSW_JSON_NAME", "")
    index_dim: int = int(os.getenv("HNSW_INDEX_DIM", "768"))
    index_space: Literal["l2", "cosine"] = os.getenv("HNSW_INDEX_SPACE", "cosine")
    index_ef: int = int(os.getenv("HNSW_INDEX_EF", "1000"))
