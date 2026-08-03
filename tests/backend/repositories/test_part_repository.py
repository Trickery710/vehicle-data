"""Tests for PartRepository, including the inventory-adjustment audit trail
and the populate_existing=True staleness regression (same bug class as
VehicleRepository.get_with_mileage/InvoiceRepository.get_with_payments)."""

from __future__ import annotations

from backend.app.models.part import Part
from backend.app.repositories.part_repository import PartRepository
from shared.mechanic_shop_shared.enums import InventoryAdjustmentReason


def _make_part(db, **overrides) -> Part:
    defaults = dict(
        part_number="BRK-001",
        description="Brake pads",
        purchase_cost=20,
        retail_price=45,
        quantity_on_hand=0,
    )
    defaults.update(overrides)
    part = Part(**defaults)
    db.add(part)
    db.flush()
    return part


def test_get_by_barcode(db) -> None:
    part = _make_part(db, barcode="012345678905")
    repo = PartRepository(db)
    found = repo.get_by_barcode("012345678905")
    assert found is not None
    assert found.id == part.id


def test_get_by_barcode_missing_returns_none(db) -> None:
    repo = PartRepository(db)
    assert repo.get_by_barcode("nonexistent") is None


def test_get_by_part_number(db) -> None:
    part = _make_part(db)
    repo = PartRepository(db)
    found = repo.get_by_part_number("BRK-001")
    assert found is not None
    assert found.id == part.id


def test_search_matches_multiple_fields(db) -> None:
    _make_part(db, part_number="BRK-001", oem_number="OEM-999", description="Brake pads")
    _make_part(db, part_number="OIL-002", oem_number="OEM-111", description="Oil filter")
    repo = PartRepository(db)

    by_number, total = repo.search("BRK-001")
    assert total == 1

    by_oem, total = repo.search("OEM-111")
    assert total == 1
    assert by_oem[0].part_number == "OIL-002"

    by_description, total = repo.search("filter")
    assert total == 1


def test_list_active_below_minimum_only(db) -> None:
    low_stock = _make_part(db, part_number="LOW-1", quantity_on_hand=1, minimum_stock=5)
    _make_part(db, part_number="OK-1", quantity_on_hand=10, minimum_stock=5)
    repo = PartRepository(db)

    items, total = repo.list_active(below_minimum_only=True)
    assert total == 1
    assert items[0].id == low_stock.id


def test_list_active_excludes_inactive(db) -> None:
    active = _make_part(db, part_number="ACTIVE-1")
    _make_part(db, part_number="INACTIVE-1", is_active=False)
    repo = PartRepository(db)

    items, total = repo.list_active()
    assert total == 1
    assert items[0].id == active.id


def test_apply_adjustment_updates_quantity_on_hand(db) -> None:
    part = _make_part(db, quantity_on_hand=5)
    repo = PartRepository(db)

    adjustment = repo.apply_adjustment(
        part, quantity_delta=3, reason=InventoryAdjustmentReason.RECEIVED_PURCHASE_ORDER.value
    )
    assert part.quantity_on_hand == 8
    assert adjustment.quantity_before == 5
    assert adjustment.quantity_after == 8
    assert adjustment.quantity_delta == 3

    repo.apply_adjustment(
        part, quantity_delta=-2, reason=InventoryAdjustmentReason.SOLD_REPAIR_ORDER.value
    )
    assert part.quantity_on_hand == 6


def test_apply_adjustment_allows_negative_delta_below_zero(db) -> None:
    """apply_adjustment itself is unconditional -- negative-stock guarding is
    a service-layer concern, so a MANUAL_COUNT_CORRECTION can always fix
    drift, including correcting into a previously-mis-tracked negative."""
    part = _make_part(db, quantity_on_hand=2)
    repo = PartRepository(db)
    repo.apply_adjustment(
        part, quantity_delta=-5, reason=InventoryAdjustmentReason.MANUAL_COUNT_CORRECTION.value
    )
    assert part.quantity_on_hand == -3


def test_get_with_adjustments_eager_loads(db) -> None:
    part = _make_part(db)
    repo = PartRepository(db)
    repo.apply_adjustment(
        part, quantity_delta=5, reason=InventoryAdjustmentReason.INITIAL_STOCK.value
    )

    found = repo.get_with_adjustments(part.id)
    assert found is not None
    assert len(found.adjustments) == 1


def test_get_with_adjustments_populate_existing_avoids_stale_read(db) -> None:
    """Regression test for the same staleness bug class documented on
    VehicleRepository.get_with_mileage: if a Part is already in the
    session's identity map with `adjustments` loaded, and a second
    adjustment is then inserted directly via apply_adjustment() (not via
    the ORM relationship's .append()), re-querying with get_with_adjustments
    in the *same* session must see the new row -- not a stale cached
    collection."""
    part = _make_part(db, quantity_on_hand=0)
    repo = PartRepository(db)

    # First load -- populates the identity map with `adjustments` eager-loaded.
    first_load = repo.get_with_adjustments(part.id)
    assert len(first_load.adjustments) == 0

    # Insert a second adjustment directly, bypassing the relationship.
    repo.apply_adjustment(
        part, quantity_delta=10, reason=InventoryAdjustmentReason.INITIAL_STOCK.value
    )

    # Re-querying in the same session must reflect the new row.
    second_load = repo.get_with_adjustments(part.id)
    assert len(second_load.adjustments) == 1
    assert second_load.quantity_on_hand == 10
