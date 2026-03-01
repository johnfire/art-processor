"""Central logger factory for theo-van-gogh."""
import logging
from datetime import datetime

from config.settings import LOGS_DIR


def configure_logging() -> None:
    """Configure the root 'theo' logger. Idempotent — safe to call multiple times."""
    root = logging.getLogger("theo")
    if root.handlers:
        return
    root.setLevel(logging.DEBUG)
    handler = logging.FileHandler(LOGS_DIR / "app.log", encoding="utf-8")
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    handler.stream.write(f"\n{'x' * 22} {now} {'x' * 22}\n")
    handler.setFormatter(logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)-28s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    ))
    root.addHandler(handler)
    root.propagate = False


def get_logger(name: str) -> logging.Logger:
    """Return a child logger under the 'theo' hierarchy.

    Example: get_logger('faso') → logger named 'theo.faso'
    """
    return logging.getLogger(f"theo.{name}")
