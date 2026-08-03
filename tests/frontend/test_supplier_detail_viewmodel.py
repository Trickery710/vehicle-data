"""Tests for SupplierDetailViewModel: create/edit and nested purchase-order list."""

from __future__ import annotations

from frontend.mechanic_shop.models.purchase_order import PurchaseOrder
from frontend.mechanic_shop.models.supplier import Supplier
from frontend.mechanic_shop.viewmodels.supplier_detail_viewmodel import SupplierDetailViewModel


def test_save_new_supplier(qtbot, fake_supplier_client) -> None:
    viewmodel = SupplierDetailViewModel(fake_supplier_client)
    viewmodel.supplier.name = "NAPA Auto Parts"

    with qtbot.waitSignal(viewmodel.saved, timeout=1000):
        viewmodel.save()

    assert viewmodel.supplier.id is not None
    assert fake_supplier_client.suppliers[viewmodel.supplier.id].name == "NAPA Auto Parts"


def test_load_existing_supplier_and_purchase_orders(qtbot, fake_supplier_client) -> None:
    fake_supplier_client.suppliers[1] = Supplier(id=1, name="NAPA Auto Parts")
    fake_supplier_client.purchase_orders_by_supplier[1] = [
        PurchaseOrder(id=1, supplier_id=1, purchase_order_number="PO-000001")
    ]
    viewmodel = SupplierDetailViewModel(fake_supplier_client, supplier_id=1)

    with qtbot.waitSignal(viewmodel.purchase_orders_loaded, timeout=1000):
        viewmodel.load()

    assert viewmodel.supplier.name == "NAPA Auto Parts"
    assert len(viewmodel.purchase_orders) == 1


def test_deactivate_supplier(qtbot, fake_supplier_client) -> None:
    fake_supplier_client.suppliers[1] = Supplier(id=1, name="NAPA Auto Parts")
    viewmodel = SupplierDetailViewModel(fake_supplier_client, supplier_id=1)

    with qtbot.waitSignal(viewmodel.supplier_loaded, timeout=1000):
        viewmodel.deactivate()

    assert viewmodel.supplier.is_active is False
