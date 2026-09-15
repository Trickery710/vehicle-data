"""Shared response envelope schemas."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Generic, TypeVar

from pydantic import BaseModel

ItemT = TypeVar("ItemT")
SchemaT = TypeVar("SchemaT", bound=BaseModel)


class PaginatedResponse(BaseModel, Generic[ItemT]):
    items: list[ItemT]
    total: int
    limit: int
    offset: int

    @classmethod
    def build(
        cls,
        rows: Iterable[Any],
        schema: type[SchemaT],
        *,
        total: int,
        limit: int,
        offset: int,
    ) -> PaginatedResponse[SchemaT]:
        """Validate ``rows`` through ``schema`` and wrap them in the envelope."""
        return PaginatedResponse[SchemaT](
            items=[schema.model_validate(row) for row in rows],
            total=total,
            limit=limit,
            offset=offset,
        )
