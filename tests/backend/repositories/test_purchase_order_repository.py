"""Tests for PurchaseOrderRepository."""

from __future__ import annotations

from backend.app.models.part import Part
from backend.app.models.purchase_order import PurchaseOrder
from backend.app.models.purchase_order_item import PurchaseOrderItem
from backend.app.models.supplier import Supplier
from backend.app.repositories.purchase_order_repository import PurchaseOrderRepository


def _make_supplier(db) -> Supplier:
    supplier = Supplier(name="NAPA Auto Parts")
    db.add(supplier)
    db.flush()
    return supplier


def _make_part(db) -> Part:
    part = Part(part_number="BRK-001", description="Brake pads")
    db.add(part)
    db.flush()
    return part


def _make_po(db, supplier, **overrides) -> PurchaseOrder:
    defaults = dict(purchase_order_number="PO-000001", supplier_id=supplier.id, status="draft")
    defaults.update(overrides)
    po = PurchaseOrder(**defaults)
    db.add(po)
    db.flush()
    return po


def test_get_by_number(db) -> None:
    supplier = _make_supplier(db)
    po = _make_po(db, supplier)
    repo = PurchaseOrderRepository(db)
    found = repo.get_by_number("PO-000001")
    assert found is not None
    assert found.id == po.id


def test_get_with_items_eager_loads(db) -> None:
    supplier = _make_supplier(db)
    part = _make_part(db)
    po = _make_po(db, supplier)
    db.add(
        PurchaseOrderItem(
            purchase_order_id=po.id, part_id=part.id, quantity_ordered=5, unit_cost=20
        )
    )
    db.flush()

    repo = PurchaseOrderRepository(db)
    found = repo.get_with_items(po.id)
    assert found is not None
    assert len(found.items) == 1


def test_list_for_supplier(db) -> None:
    supplier = _make_supplier(db)
    other_supplier = _make_supplier(db)
    po1 = _make_po(db, supplier, purchase_order_number="PO-000001")
    _make_po(db, other_supplier, purchase_order_number="PO-000002")
    repo = PurchaseOrderRepository(db)

    results = repo.list_for_supplier(supplier.id)
    assert [po.id for po in results] == [po1.id]


def test_list_all_filters_by_status(db) -> None:
    supplier = _make_supplier(db)
    _make_po(db, supplier, purchase_order_number="PO-000001", status="draft")
    _make_po(db, supplier, purchase_order_number="PO-000002", status="received")
    repo = PurchaseOrderRepository(db)

    items, total = repo.list_all(status="received")
    assert total == 1
    assert items[0].purchase_order_number == "PO-000002"


def test_search_matches_number(db) -> None:
    supplier = _make_supplier(db)
    _make_po(db, supplier, purchase_order_number="PO-000042")
    repo = PurchaseOrderRepository(db)

    items, total = repo.search("000042")
    assert total == 1
