"""Human-readable document numbering (RO-000001, INV-000001, EST-000001).

``next_number`` performs one atomic ``UPDATE ... RETURNING`` statement --
safe under this app's single-process/SQLite-write-serialization concurrency
model (SQLite takes a write lock at the transaction's first write
statement; this app runs a single local FastAPI process serving one
desktop client, not multiple worker processes).
"""

from __future__ import annotations

from sqlalchemy import update

from backend.app.core.exceptions import NotFoundError
from backend.app.models.number_sequence import NumberSequence
from backend.app.repositories.base import BaseRepository


class NumberSequenceRepository(BaseRepository[NumberSequence]):
    model = NumberSequence

    def next_number(self, entity_type: str) -> str:
        stmt = (
            update(NumberSequence)
            .where(NumberSequence.entity_type == entity_type)
            .values(next_value=NumberSequence.next_value + 1)
            .returning(NumberSequence.next_value, NumberSequence.prefix)
        )
        row = self.db.execute(stmt).first()
        if row is None:
            raise NotFoundError(f"No number sequence configured for entity type '{entity_type}'")
        new_value, prefix = row
        issued_value = new_value - 1
        return f"{prefix}-{issued_value:06d}"
