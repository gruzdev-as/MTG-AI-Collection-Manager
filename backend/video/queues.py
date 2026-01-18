from queue import Queue

import numpy as np


class FrameQueues:
    """Queue manager class."""

    def __init__(self, queue_dict: dict[str, Queue]) -> None:
        self.queue_dict = queue_dict

    def get(self, queue_name: str) -> np.ndarray:
        """Get item from the called queue."""
        if queue_name not in self.queue_dict:
            error_msg = f"{queue_name} not in queue dict keys: {self.queue_dict.keys()}"
            raise KeyError(error_msg)
        return self.queue_dict[queue_name].get()

    def put(self, queue_name: str, item: np.ndarray) -> None:
        """Put item into the called queue."""
        if queue_name not in self.queue_dict:
            error_msg = f"{queue_name} not in queue dict keys: {self.queue_dict.keys()}"
            raise KeyError(error_msg)
        self.queue_dict[queue_name].put(item)
