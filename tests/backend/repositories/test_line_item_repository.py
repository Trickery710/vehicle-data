"""Tests for LineItemRepository against a real (temp) SQLite database."""

from __future__ import annotations

from backend.app.models.line_item import LineItem
from backend.app.repositories.line_item_repository import LineItemRepository
from shared.mechanic_shop_shared.enums import EntityType, LineItemType


def _make_item(entity_type: str, entity_id: int, **overrides) -> LineItem:
    defaults = dict(
        entity_type=entity_type,
        entity_id=entity_id,
        line_type=LineItemType.PART.value,
        description="Widget",
        quantity=1,
        unit_price=10,
    )
    defaults.update(overrides)
    return LineItem(**defaults)


def test_list_for_entity_scoped_correctly(db) -> None:
    repo = LineItemRepository(db)
    db.add(_make_item(EntityType.ESTIMATE.value, 1, description="A"))
    db.add(_make_item(EntityType.ESTIMATE.value, 2, description="B"))
    db.add(_make_item(EntityType.REPAIR_ORDER.value, 1, description="C"))
    db.flush()

    items = repo.list_for_entity(EntityType.ESTIMATE.value, 1)
    assert [i.description for i in items] == ["A"]


def test_line_total_computed_property() -> None:
    item = LineItem(
        entity_type="estimate",
        entity_id=1,
        line_type="labor",
        description="x",
        quantity=2,
        unit_price=50,
    )
    assert item.line_total == 100


def test_replace_for_entity_deletes_old_and_inserts_new(db) -> None:
    repo = LineItemRepository(db)
    repo.replace_for_entity(
        EntityType.ESTIMATE.value, 1, [_make_item(EntityType.ESTIMATE.value, 1, description="Old")]
    )
    assert [i.description for i in repo.list_for_entity(EntityType.ESTIMATE.value, 1)] == ["Old"]

    repo.replace_for_entity(
        EntityType.ESTIMATE.value,
        1,
        [
            _make_item(EntityType.ESTIMATE.value, 1, description="New1"),
            _make_item(EntityType.ESTIMATE.value, 1, description="New2"),
        ],
    )
    descriptions = {i.description for i in repo.list_for_entity(EntityType.ESTIMATE.value, 1)}
    assert descriptions == {"New1", "New2"}


def test_copy_for_entity_creates_independent_rows(db) -> None:
    repo = LineItemRepository(db)
    repo.replace_for_entity(
        EntityType.ESTIMATE.value,
        1,
        [_make_item(EntityType.ESTIMATE.value, 1, description="Original", unit_price=20)],
    )

    repo.copy_for_entity(EntityType.ESTIMATE.value, 1, EntityType.REPAIR_ORDER.value, 99)

    source = repo.list_for_entity(EntityType.ESTIMATE.value, 1)
    copies = repo.list_for_entity(EntityType.REPAIR_ORDER.value, 99)
    assert len(source) == 1 and len(copies) == 1
    assert source[0].id != copies[0].id
    assert copies[0].description == "Original"
    assert copies[0].unit_price == 20

    # mutating the copy must never affect the source (copy, not repoint)
    copies[0].unit_price = 999
    db.flush()
    source_again = repo.list_for_entity(EntityType.ESTIMATE.value, 1)
    assert source_again[0].unit_price == 20
