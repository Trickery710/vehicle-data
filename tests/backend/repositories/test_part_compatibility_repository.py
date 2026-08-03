"""Tests for PartCompatibilityRepository's wholesale-replace semantics."""

from __future__ import annotations

from backend.app.models.part import Part
from backend.app.models.part_compatibility import PartCompatibility
from backend.app.repositories.part_compatibility_repository import PartCompatibilityRepository


def _make_part(db) -> Part:
    part = Part(part_number="BRK-001", description="Brake pads")
    db.add(part)
    db.flush()
    return part


def test_replace_for_part_wholesale_replace(db) -> None:
    part = _make_part(db)
    repo = PartCompatibilityRepository(db)

    repo.replace_for_part(
        part.id, [PartCompatibility(make="Honda", model="Accord", year_start=2003, year_end=2007)]
    )
    assert len(repo.list_for_part(part.id)) == 1

    repo.replace_for_part(
        part.id,
        [
            PartCompatibility(make="Honda", model="Civic"),
            PartCompatibility(make="Toyota", model=None, notes="fits all Toyota"),
        ],
    )
    items = repo.list_for_part(part.id)
    assert len(items) == 2
    assert {i.make for i in items} == {"Honda", "Toyota"}


def test_replace_for_part_empty_list_clears(db) -> None:
    part = _make_part(db)
    repo = PartCompatibilityRepository(db)
    repo.replace_for_part(part.id, [PartCompatibility(make="Honda", model="Accord")])
    assert len(repo.list_for_part(part.id)) == 1

    repo.replace_for_part(part.id, [])
    assert len(repo.list_for_part(part.id)) == 0
