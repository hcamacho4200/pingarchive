"""Setup logging for the application"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_name: str = "pingarchive", log_dir: str = "logs", level: int = logging.INFO):
    """Setup logging for the application"""
    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    log_file = log_path / f"{log_name}.log"

    # Root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Prevent duplicate handlers if setup is called multiple times
    if logger.handlers:
        return

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # ---- Console Handler ----
    console_handler = logging.StreamHandler(sys.__stderr__)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    # ---- File Handler (rotating) ----
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
    )
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)


def reset_logging():
    """Reset logging before setting up"""
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
        handler.close()

    root.setLevel(logging.NOTSET)


setup_logging()
