"""Logging setup: console + rotating file handler under the app's data dir."""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler

from backend.app.config import get_settings


def configure_logging() -> None:
    settings = get_settings()
    root_logger = logging.getLogger()
    if root_logger.handlers:
        return  # already configured (e.g. re-entrant reload)

    root_logger.setLevel(settings.log_level)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    file_handler = RotatingFileHandler(settings.log_file_path(), maxBytes=5_000_000, backupCount=3)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
