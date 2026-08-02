"""SQLAlchemy engine/session setup, with SQLite pragmas required for correctness.

Two pragmas matter here:

* ``foreign_keys=ON`` -- SQLite disables foreign-key enforcement by default.
  Without this, every ``ondelete="CASCADE"``/``"RESTRICT"`` clause declared on
  the models is silently unenforced.
* ``journal_mode=WAL`` -- better read/write concurrency, relevant once
  multiple technicians' clients hit the same backend over a LAN.
"""

from collections.abc import Generator

from sqlalchemy import Engine, create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import get_settings

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _apply_sqlite_pragmas(dbapi_connection, _connection_record) -> None:
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        url = settings.resolved_database_url()
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        _engine = create_engine(url, connect_args=connect_args)
        if url.startswith("sqlite"):
            event.listen(_engine, "connect", _apply_sqlite_pragmas)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
    return _session_factory


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a request-scoped session.

    Commits automatically if the route handler completes without raising,
    and rolls back otherwise -- routers/services never call commit/rollback
    themselves, so a raised ``DomainError`` can never leave a partial write
    committed.
    """
    session_factory = get_session_factory()
    db = session_factory()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def reset_engine_for_testing() -> None:
    """Drops the cached engine/session factory so tests can point at a fresh DB."""
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None
