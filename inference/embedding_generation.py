import logging
from pathlib import Path

import numpy as np
import torch
from transformers import AutoImageProcessor, AutoModel, DINOv3ViTModel
from transformers import DINOv3ViTImageProcessorFast as DINOv3ViTImageProcessor

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """Generate cropped image embedding using DINOV3."""

    def __init__(self, model_path: Path) -> None:
        self.model: DINOv3ViTModel = AutoModel.from_pretrained(model_path, local_files_only=True)
        self.processor: DINOv3ViTImageProcessor = AutoImageProcessor.from_pretrained(model_path, local_files_only=True)
        self.device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
        self.model.to(self.device)
        logger.info("Model has loaded")

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

        image_features = self.model(**inputs).pooler_output
        image_features = image_features / image_features.norm(dim=1, keepdim=True)

        return image_features.cpu().numpy()
