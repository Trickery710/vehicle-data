"""Shared fixtures for backend tests.

Each test gets a fresh temp-file SQLite database with the *real* Alembic
migration chain applied (not ``Base.metadata.create_all()``), so migration
correctness itself is exercised, not just the end-state schema.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.config import get_settings
from backend.app.db import session as db_session_module
from backend.app.db.init_db import run_migrations
from backend.app.main import create_app


@pytest.fixture()
def _fresh_test_database(tmp_path, monkeypatch) -> Generator[None, None, None]:
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("MSM_DATABASE_URL", f"sqlite:///{db_path}")
    get_settings.cache_clear()
    db_session_module.reset_engine_for_testing()
    run_migrations()
    yield
    db_session_module.reset_engine_for_testing()
    get_settings.cache_clear()


@pytest.fixture()
def db(_fresh_test_database) -> Generator[Session, None, None]:
    """A raw SQLAlchemy session against the fresh test database, for
    repository/service-layer tests that don't need the HTTP layer."""
    session_factory = db_session_module.get_session_factory()
    session = session_factory()
    try:
        yield session
        session.commit()
    finally:
        session.close()


@pytest.fixture()
def client(_fresh_test_database) -> Generator[TestClient, None, None]:
    """A ``TestClient`` for full-stack API tests. Runs the app's real
    lifespan (which re-runs ``alembic upgrade head`` -- a harmless no-op
    since ``_fresh_test_database`` already applied it)."""
    app = create_app()
    with TestClient(app) as test_client:
        yield test_client
