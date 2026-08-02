"""Tests for EstimateDetailViewModel: load/save, line items, status
transitions, and conversion to a repair order."""

from __future__ import annotations

from frontend.mechanic_shop.models.estimate import Estimate
from frontend.mechanic_shop.models.line_item import LineItem
from frontend.mechanic_shop.viewmodels.estimate_detail_viewmodel import EstimateDetailViewModel


def test_save_new_estimate_calls_create(qtbot, fake_estimate_client) -> None:
    viewmodel = EstimateDetailViewModel(fake_estimate_client, vehicle_id=1)
    viewmodel.estimate.title = "Brake job"

    with qtbot.waitSignal(viewmodel.saved, timeout=1000):
        viewmodel.save()

    assert viewmodel.estimate.id is not None
    assert viewmodel.is_new is False
    assert fake_estimate_client.estimates[viewmodel.estimate.id].title == "Brake job"


def test_load_existing_estimate_and_line_items(qtbot, fake_estimate_client) -> None:
    fake_estimate_client.estimates[1] = Estimate(id=1, vehicle_id=1, title="Existing")
    fake_estimate_client.line_items[1] = [
        LineItem(id=1, description="Labor", quantity=1, unit_price=100, line_total=100)
    ]
    viewmodel = EstimateDetailViewModel(fake_estimate_client, vehicle_id=1, estimate_id=1)

    with qtbot.waitSignal(viewmodel.line_items_loaded, timeout=1000):
        viewmodel.load()

    assert viewmodel.estimate.title == "Existing"
    assert len(viewmodel.line_items) == 1


def test_replace_line_items(qtbot, fake_estimate_client) -> None:
    fake_estimate_client.estimates[1] = Estimate(id=1, vehicle_id=1)
    fake_estimate_client.line_items[1] = []
    viewmodel = EstimateDetailViewModel(fake_estimate_client, vehicle_id=1, estimate_id=1)

    new_items = [LineItem(id=None, description="Part", unit_price=45)]
    with qtbot.waitSignal(viewmodel.line_items_loaded, timeout=1000):
        viewmodel.replace_line_items(new_items)

    assert fake_estimate_client.line_items[1] == new_items
    assert viewmodel.line_items == new_items


def test_send_approve_decline_transitions(qtbot, fake_estimate_client) -> None:
    fake_estimate_client.estimates[1] = Estimate(id=1, vehicle_id=1, status="draft")
    viewmodel = EstimateDetailViewModel(fake_estimate_client, vehicle_id=1, estimate_id=1)

    with qtbot.waitSignal(viewmodel.estimate_loaded, timeout=1000):
        viewmodel.send_estimate()
    assert viewmodel.estimate.status == "sent"

    with qtbot.waitSignal(viewmodel.estimate_loaded, timeout=1000):
        viewmodel.approve_estimate(signer_name="Jane Doe")
    assert viewmodel.estimate.status == "approved"


def test_convert_to_repair_order(qtbot, fake_estimate_client) -> None:
    fake_estimate_client.estimates[1] = Estimate(id=1, vehicle_id=1)
    viewmodel = EstimateDetailViewModel(fake_estimate_client, vehicle_id=1, estimate_id=1)

    with qtbot.waitSignal(viewmodel.converted, timeout=1000) as blocker:
        viewmodel.convert_to_repair_order()

    assert blocker.args == [999]
    assert fake_estimate_client.convert_calls == [1]
