from dataclasses import dataclass
from pathlib import Path
from typing import Literal


@dataclass(frozen=True)
class InferenceConfig:
    """Configure inference."""

    model_path: Path = Path("inference/data/CLIP")


@dataclass(frozen=True)
class HNSWConfig:
    """Configure HNSW index."""

    index_path: Path = Path("inference/data/hnsw/hnsw_index_cos.bin")
    index_json_path: Path = Path("inference/data/hnsw/image_metadata.json")
    index_dim: int = 768
    index_space: Literal["cosine", "l2"] = "cosine"
    index_ef: int = 100
