"""Generic CRUD repository base class."""

from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from backend.app.db.base import Base

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, db: Session) -> None:
        self.db = db

    # -- shared query helpers ------------------------------------------------
    # Defined before ``list()`` so the builtin ``list`` stays in scope for
    # their return annotations.

    def _first(self, *criteria: Any) -> ModelT | None:
        """First row of ``self.model`` matching all ``criteria`` (or None)."""
        return self.db.scalars(select(self.model).where(*criteria)).first()

    def _count(self, base: Select[Any]) -> int:
        """Total row count for a pre-pagination SELECT."""
        return self.db.scalar(select(func.count()).select_from(base.subquery())) or 0

    def _paginate(
        self, base: Select[tuple[ModelT]], *order_by: Any, limit: int, offset: int
    ) -> tuple[list[ModelT], int]:
        """Return ``(page_items, total_count)`` for a filtered ``base`` SELECT.

        ``total_count`` reflects ``base`` before ordering/pagination; the page
        applies ``order_by`` then ``limit``/``offset``.
        """
        total = self._count(base)
        items = list(self.db.scalars(base.order_by(*order_by).limit(limit).offset(offset)))
        return items, total

    # -- CRUD --------------------------------------------------------------

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
