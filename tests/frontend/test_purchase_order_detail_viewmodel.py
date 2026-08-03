"""Tests for PurchaseOrderDetailViewModel: create, receive, return, cancel."""

from __future__ import annotations

from frontend.mechanic_shop.models.purchase_order import PurchaseOrder, PurchaseOrderItem
from frontend.mechanic_shop.viewmodels.purchase_order_detail_viewmodel import (
    PurchaseOrderDetailViewModel,
)


def test_save_new_purchase_order_with_items(
    qtbot, fake_purchase_order_client, fake_supplier_client
) -> None:
    viewmodel = PurchaseOrderDetailViewModel(
        fake_purchase_order_client, fake_supplier_client, supplier_id=1
    )
    viewmodel.purchase_order.items = [
        PurchaseOrderItem(id=None, part_id=1, quantity_ordered=10, unit_cost=20)
    ]

    with qtbot.waitSignal(viewmodel.saved, timeout=1000):
        viewmodel.save()

    assert viewmodel.purchase_order.id is not None
    assert viewmodel.purchase_order.purchase_order_number == "PO-000001"


def test_mark_ordered(qtbot, fake_purchase_order_client, fake_supplier_client) -> None:
    fake_purchase_order_client.purchase_orders[1] = PurchaseOrder(
        id=1, supplier_id=1, purchase_order_number="PO-000001", status="draft"
    )
    viewmodel = PurchaseOrderDetailViewModel(
        fake_purchase_order_client, fake_supplier_client, purchase_order_id=1
    )

    with qtbot.waitSignal(viewmodel.purchase_order_loaded, timeout=1000):
        viewmodel.mark_ordered()

    assert viewmodel.purchase_order.status == "ordered"


def test_receive_items(qtbot, fake_purchase_order_client, fake_supplier_client) -> None:
    fake_purchase_order_client.purchase_orders[1] = PurchaseOrder(
        id=1, supplier_id=1, purchase_order_number="PO-000001", status="ordered"
    )
    viewmodel = PurchaseOrderDetailViewModel(
        fake_purchase_order_client, fake_supplier_client, purchase_order_id=1
    )

    with qtbot.waitSignal(viewmodel.purchase_order_loaded, timeout=1000):
        viewmodel.receive_items([{"purchase_order_item_id": 1, "quantity": 5}])

    assert viewmodel.purchase_order.status == "received"
    assert fake_purchase_order_client.receive_calls == [
        (1, [{"purchase_order_item_id": 1, "quantity": 5}])
    ]


def test_record_return(qtbot, fake_purchase_order_client, fake_supplier_client) -> None:
    fake_purchase_order_client.purchase_orders[1] = PurchaseOrder(
        id=1, supplier_id=1, purchase_order_number="PO-000001", status="received"
    )
    viewmodel = PurchaseOrderDetailViewModel(
        fake_purchase_order_client, fake_supplier_client, purchase_order_id=1
    )

    with qtbot.waitSignal(viewmodel.purchase_order_loaded, timeout=1000):
        viewmodel.record_return(part_id=1, quantity=2, notes="defective")

    assert fake_purchase_order_client.return_calls == [(1, 1, 2)]


def test_cancel(qtbot, fake_purchase_order_client, fake_supplier_client) -> None:
    fake_purchase_order_client.purchase_orders[1] = PurchaseOrder(
        id=1, supplier_id=1, purchase_order_number="PO-000001", status="draft"
    )
    viewmodel = PurchaseOrderDetailViewModel(
        fake_purchase_order_client, fake_supplier_client, purchase_order_id=1
    )

    with qtbot.waitSignal(viewmodel.purchase_order_loaded, timeout=1000):
        viewmodel.cancel()

    assert viewmodel.purchase_order.status == "cancelled"
