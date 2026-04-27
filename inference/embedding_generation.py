from pathlib import Path

import numpy as np
import torch
from transformers import CLIPModel, CLIPProcessor


class EmbeddingGenerator:
    """Generate cropped image embedding using CLIP."""

    def __init__(self, model_path: Path) -> None:
        self.model: CLIPModel = CLIPModel.from_pretrained(model_path, local_files_only=True)
        self.processor: CLIPProcessor = CLIPProcessor.from_pretrained(model_path, local_files_only=True)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model.to(self.device)
        print("Model has loaded")

    @torch.inference_mode()
    def generate_image_embedding(self, images: np.ndarray) -> np.ndarray:
        """Use CLIP to generate embedding vectors.

        Args:
            images (np.ndarray): The warped image

        Returns:
            np.array: Generated embedding

        """
        inputs = self.processor(images=[images], return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        image_features = self.model.get_image_features(**inputs)
        image_features = image_features / image_features.norm(dim=1, keepdim=True)

        return image_features.cpu().numpy()
