"""Generic CRUD repository base class."""

from __future__ import annotations

from typing import Generic, TypeVar

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, entity_id: int) -> ModelT | None:
        return self.db.get(self.model, entity_id)

    def list(self, limit: int = 50, offset: int = 0) -> tuple[list[ModelT], int]:
        total = self.db.scalar(select(func.count()).select_from(self.model)) or 0
        # Every concrete model defines an `id` primary key column; `Base`
        # itself doesn't declare one (it's abstract), so mypy can't see it
        # through the bound TypeVar.
        order_column = self.model.id  # type: ignore[attr-defined]
        items = list(
            self.db.scalars(select(self.model).limit(limit).offset(offset).order_by(order_column))
        )
        return items, total

    def add(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.flush()
        self.db.refresh(obj)
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.flush()
