"""Logger configuration utility."""
import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logger(
    name: str = "openlibrary_automation",
    level: int = logging.INFO,
    log_file: bool = True
) -> logging.Logger:
    """
    Set up and configure logger.

    Args:
        name: Logger name
        level: Logging level
        log_file: Whether to create a log file

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Clear existing handlers
    logger.handlers = []

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    # File handler
    if log_file:
        log_dir = Path("reports/logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        file_handler = logging.FileHandler(
            log_dir / f"test_run_{timestamp}.log",
            encoding="utf-8"
        )
        file_handler.setLevel(level)
        file_format = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_format)
        logger.addHandler(file_handler)

    return logger


# Create default logger
default_logger = setup_logger()
