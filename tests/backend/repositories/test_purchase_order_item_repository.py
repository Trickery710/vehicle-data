"""Tests for PurchaseOrderItemRepository."""

from __future__ import annotations

from backend.app.models.part import Part
from backend.app.models.purchase_order import PurchaseOrder
from backend.app.models.purchase_order_item import PurchaseOrderItem
from backend.app.models.supplier import Supplier
from backend.app.repositories.purchase_order_item_repository import PurchaseOrderItemRepository


def _make_supplier(db) -> Supplier:
    supplier = Supplier(name="NAPA Auto Parts")
    db.add(supplier)
    db.flush()
    return supplier


def _make_part(db, **overrides) -> Part:
    defaults = dict(part_number="BRK-001", description="Brake pads")
    defaults.update(overrides)
    part = Part(**defaults)
    db.add(part)
    db.flush()
    return part


def _make_po(db, supplier) -> PurchaseOrder:
    po = PurchaseOrder(purchase_order_number="PO-000001", supplier_id=supplier.id, status="draft")
    db.add(po)
    db.flush()
    return po


def test_add_items_sets_sort_order_and_purchase_order_id(db) -> None:
    supplier = _make_supplier(db)
    po = _make_po(db, supplier)
    part1 = _make_part(db, part_number="BRK-001")
    part2 = _make_part(db, part_number="OIL-002")
    repo = PurchaseOrderItemRepository(db)

    items = repo.add_items(
        po.id,
        [
            PurchaseOrderItem(part_id=part1.id, quantity_ordered=5, unit_cost=20),
            PurchaseOrderItem(part_id=part2.id, quantity_ordered=3, unit_cost=8),
        ],
    )
    assert [i.sort_order for i in items] == [0, 1]
    assert all(i.purchase_order_id == po.id for i in items)


def test_list_for_purchase_order_ordered_by_sort_order(db) -> None:
    supplier = _make_supplier(db)
    po = _make_po(db, supplier)
    part = _make_part(db)
    repo = PurchaseOrderItemRepository(db)
    repo.add_items(po.id, [PurchaseOrderItem(part_id=part.id, quantity_ordered=1, unit_cost=10)])

    items = repo.list_for_purchase_order(po.id)
    assert len(items) == 1
    assert items[0].part_id == part.id
