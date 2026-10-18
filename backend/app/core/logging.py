import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from app.core.config import settings


def setup_logging() -> logging.Logger:
    """
    Configure application-wide logging.

    Logs are written to:
    1. Console
    2. Rotating log file
    """

    log_directory = Path(settings.log_directory)
    log_directory.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("marketmind")
    logger.setLevel(settings.log_level.upper())

    # Prevent duplicate handlers if this function is called again.
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # File handler
    file_handler = RotatingFileHandler(
        log_directory / "marketmind.log",
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logging()