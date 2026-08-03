"""Tests for RepairOrderDetailViewModel: load/save, line items, checklist,
signatures, status updates, and conversion to an invoice."""

from __future__ import annotations

from frontend.mechanic_shop.models.line_item import LineItem
from frontend.mechanic_shop.models.repair_order import InspectionChecklistItem, RepairOrder
from frontend.mechanic_shop.models.signature import Signature
from frontend.mechanic_shop.viewmodels.repair_order_detail_viewmodel import (
    RepairOrderDetailViewModel,
)


def test_save_new_repair_order_calls_create(qtbot, fake_repair_order_client) -> None:
    viewmodel = RepairOrderDetailViewModel(fake_repair_order_client, vehicle_id=1)
    viewmodel.repair_order.complaint = "Squeaky brakes"

    with qtbot.waitSignal(viewmodel.saved, timeout=1000):
        viewmodel.save()

    assert viewmodel.repair_order.id is not None
    assert viewmodel.is_new is False
    saved = fake_repair_order_client.repair_orders[viewmodel.repair_order.id]
    assert saved.complaint == "Squeaky brakes"


def test_load_existing_repair_order_loads_line_items_and_signatures(
    qtbot, fake_repair_order_client
) -> None:
    fake_repair_order_client.repair_orders[1] = RepairOrder(id=1, vehicle_id=1, complaint="Test")
    fake_repair_order_client.line_items[1] = [LineItem(id=1, description="Labor", unit_price=100)]
    fake_repair_order_client.signatures[1] = [
        Signature(id=1, signer_role="customer", signer_name="Jane Doe")
    ]
    viewmodel = RepairOrderDetailViewModel(
        fake_repair_order_client, vehicle_id=1, repair_order_id=1
    )

    with qtbot.waitSignal(viewmodel.signatures_loaded, timeout=1000):
        viewmodel.load()

    assert viewmodel.repair_order.complaint == "Test"
    assert len(viewmodel.line_items) == 1
    assert len(viewmodel.signatures) == 1


def test_update_status_sets_new_status(qtbot, fake_repair_order_client) -> None:
    fake_repair_order_client.repair_orders[1] = RepairOrder(id=1, vehicle_id=1, status="estimate")
    viewmodel = RepairOrderDetailViewModel(
        fake_repair_order_client, vehicle_id=1, repair_order_id=1
    )

    with qtbot.waitSignal(viewmodel.repair_order_loaded, timeout=1000):
        viewmodel.update_status("in_progress")

    assert viewmodel.repair_order.status == "in_progress"


def test_replace_checklist_items(qtbot, fake_repair_order_client) -> None:
    fake_repair_order_client.repair_orders[1] = RepairOrder(id=1, vehicle_id=1)
    viewmodel = RepairOrderDetailViewModel(
        fake_repair_order_client, vehicle_id=1, repair_order_id=1
    )

    items = [InspectionChecklistItem(id=None, item_description="Check brakes", result="pass")]
    with qtbot.waitSignal(viewmodel.repair_order_loaded, timeout=1000):
        viewmodel.replace_checklist_items(items)

    assert viewmodel.repair_order.checklist_items == items


def test_add_signature_reloads_signatures(qtbot, fake_repair_order_client) -> None:
    fake_repair_order_client.repair_orders[1] = RepairOrder(id=1, vehicle_id=1)
    fake_repair_order_client.signatures[1] = []
    viewmodel = RepairOrderDetailViewModel(
        fake_repair_order_client, vehicle_id=1, repair_order_id=1
    )

    signature = Signature(id=None, signer_role="customer", signer_name="Jane Doe")
    with qtbot.waitSignal(viewmodel.signatures_loaded, timeout=1000):
        viewmodel.add_signature(signature)

    assert len(viewmodel.signatures) == 1
    assert viewmodel.signatures[0].signer_name == "Jane Doe"


def test_convert_to_invoice(qtbot, fake_repair_order_client) -> None:
    fake_repair_order_client.repair_orders[1] = RepairOrder(id=1, vehicle_id=1)
    viewmodel = RepairOrderDetailViewModel(
        fake_repair_order_client, vehicle_id=1, repair_order_id=1
    )

    with qtbot.waitSignal(viewmodel.converted, timeout=1000) as blocker:
        viewmodel.convert_to_invoice(tax_rate=8.25)

    assert blocker.args == [999]
    assert fake_repair_order_client.convert_calls == [1]


def test_add_part_from_inventory_reloads_line_items(qtbot, fake_repair_order_client) -> None:
    fake_repair_order_client.repair_orders[1] = RepairOrder(id=1, vehicle_id=1)
    fake_repair_order_client.line_items[1] = []
    viewmodel = RepairOrderDetailViewModel(
        fake_repair_order_client, vehicle_id=1, repair_order_id=1
    )

    with qtbot.waitSignal(viewmodel.line_items_loaded, timeout=1000):
        viewmodel.add_part_from_inventory(part_id=5, quantity=2, unit_price=45)

    assert len(viewmodel.line_items) == 1
    assert viewmodel.line_items[0].part_id == 5
    assert fake_repair_order_client.add_part_calls == [(1, 5, 2, 45)]
