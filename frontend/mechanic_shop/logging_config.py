"""Logging setup for the frontend process (separate log file from the backend)."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from frontend.mechanic_shop.config import data_dir


def configure_logging() -> None:
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return

    root_logger.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(
        data_dir() / "frontend.log", maxBytes=5_000_000, backupCount=3
    )
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
