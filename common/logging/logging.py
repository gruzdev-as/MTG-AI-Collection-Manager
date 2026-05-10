import logging
import sys


def setup_logging() -> None:
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)-30s | %(message)s",
        "%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    for name in (
        "uvicorn",
        "uvicorn.error",
        "uvicorn.access",
        "apscheduler",
    ):
        logger = logging.getLogger(name)
        logger.handlers.clear()
        logger.propagate = True
