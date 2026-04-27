import json
from pathlib import Path
from typing import Literal

import hnswlib
from numpy import ndarray


class HNSWSearchTool:
    """Nearest neigbour searching tool."""

    def __init__(
        self,
        index_dim: int,
        index_space: Literal["cosine", "l2"],
        index_path: Path,
        index_ef: int,
        index_json_path: Path,
    ) -> None:
        self.hnsw_index = hnswlib.Index(space=index_space, dim=index_dim)
        self.hnsw_index.load_index(str(index_path))
        self.hnsw_index.set_ef(index_ef)

        with Path(index_json_path).open("r") as f:
            self.image_metadata = json.load(f)

        print("Search Engine has loaded")

    def search_in_hnsw(self, query_embedding: ndarray) -> list[dict[str, str]]:
        """Use hnsw index to retrieval info."""
        labels, _ = self.hnsw_index.knn_query(query_embedding, k=5)

        return [self.image_metadata[str(label)] for label in labels[0]]
