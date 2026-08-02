"""Tests for NumberSequenceRepository -- the atomic document-numbering counter."""

from __future__ import annotations

import pytest

from backend.app.core.exceptions import NotFoundError
from backend.app.models.number_sequence import NumberSequence
from backend.app.repositories.number_sequence_repository import NumberSequenceRepository


def test_next_number_is_monotonic_and_unique(db) -> None:
    db.add(NumberSequence(entity_type="widget", prefix="WID", next_value=1))
    db.flush()
    repo = NumberSequenceRepository(db)

    first = repo.next_number("widget")
    second = repo.next_number("widget")
    third = repo.next_number("widget")

    assert first == "WID-000001"
    assert second == "WID-000002"
    assert third == "WID-000003"
    assert len({first, second, third}) == 3


def test_next_number_unknown_entity_type_raises(db) -> None:
    repo = NumberSequenceRepository(db)
    with pytest.raises(NotFoundError):
        repo.next_number("does_not_exist")


def test_seeded_sequences_from_migration_work(db) -> None:
    """The Phase 2 migration seeds estimate/repair_order/invoice rows."""
    repo = NumberSequenceRepository(db)
    assert repo.next_number("estimate") == "EST-000001"
    assert repo.next_number("repair_order") == "RO-000001"
    assert repo.next_number("invoice") == "INV-000001"
