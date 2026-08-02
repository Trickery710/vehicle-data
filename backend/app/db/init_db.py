"""Programmatic ``alembic upgrade head``, run automatically on app startup.

This is a deliberate trade-off: proper Alembic hygiene says migrations
should be run explicitly, but a non-technical shop owner should never need
to run a CLI command. Auto-migrating on every launch keeps the schema
current with zero user action, while still going through real migrations
(not ``create_all``) so the upgrade path is identical to what a developer
tests locally.
"""

from __future__ import annotations

import logging
from pathlib import Path

from alembic.config import Config

from alembic import command

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[3]


def run_migrations() -> None:
    alembic_ini = _PROJECT_ROOT / "alembic.ini"
    cfg = Config(str(alembic_ini))
    cfg.set_main_option("script_location", str(_PROJECT_ROOT / "alembic"))
    logger.info("Running database migrations (alembic upgrade head)...")
    command.upgrade(cfg, "head")
    logger.info("Database migrations complete.")
